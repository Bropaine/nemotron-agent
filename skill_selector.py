import json
from ollama import Client


def select_skill(
        client: Client,
        request: str,
        catalog: dict[str, dict[str, str]],
) -> str:
    response = client.chat(
        model="nemotron-3-nano:30b",
        messages=[
            {
                "role": "system",
                "content": (
                        "Choose one exact skill ID from the catalog below. "
                        "Never invent a skill ID. "
                        "If the task is not covered by a listed skill, reply NONE. "
                        "Reply with only the ID or NONE, without explanation.\n\n"
                        + json.dumps(catalog)
                ),
            },
            {"role": "user", "content": request},
        ],
        options={"num_ctx": 4096},
    )
    return response.message.content.strip()