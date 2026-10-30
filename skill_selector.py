import json
from ollama import Client


def select_skill(
        client: Client,
        request: str,
        catalog: dict[str, dict[str, str]],
) -> str:
    allowed_ids = [*catalog, "NONE"]
    schema = {
        "type": "object",
        "properties": {
            "skill_id": {
                "type": "string",
                "enum": allowed_ids,
            }
        },
        "required": ["skill_id"],
        "additionalProperties": False,
    }

    response = client.chat(
        model="nemotron-3-nano:30b",
        messages=[
            {
                "role": "system",
                "content": (
                        "You classify requests into skills. "
                        "Do not answer or carry out the request. "
                        "Tool names in the request are not skill IDs. "
                        "Choose the catalog skill whose description best fits. "
                        "Choose NONE only when no skill fits. "
                        "Return JSON matching this schema:\n"
                        + json.dumps(schema)
                        + "\n\nSkill catalog:\n"
                        + json.dumps(catalog)
                ),
            },
            {"role": "user", "content": request},
        ],
        format=schema,
        options={"num_ctx": 4096, "temperature": 0},
    )

    try:
        selection = json.loads(response.message.content)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("Skill selector returned invalid JSON.") from error

    if (
            not isinstance(selection, dict)
            or set(selection) != {"skill_id"}
            or not isinstance(selection["skill_id"], str)
            or selection["skill_id"] not in allowed_ids
    ):
        raise ValueError("Skill selector returned an invalid selection.")

    return selection["skill_id"]