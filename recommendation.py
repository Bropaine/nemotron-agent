import json
from ollama import Client


def choose_recommendation(
        client: Client,
        messages: list,
        read_urls: set[str],
) -> dict:
    schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": ["string", "null"],
                "enum": [*sorted(read_urls), None],
            },
            "title": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["url", "title", "reason"],
        "additionalProperties": False,
    }

    response = client.chat(
        model="nemotron-3-nano:30b",
        messages=messages + [{
            "role": "user",
            "content": (
                    "Evaluate the successfully read pages against the user's "
                    "original request. Match both the topic and the requested "
                    "kind of information. Sharing a topic is not enough. "
                    "For example, a list of names does not by itself explain "
                    "historical development. "
                    "Choose a page only if its returned text directly supports "
                    "a useful answer to that request. Do not assume missing or "
                    "truncated sections contain the needed information. "
                    "Base the title and short reason on the returned page text. "
                    "Preserve important source-quality warnings. "
                    "If no read page meets the request, set url to null, title "
                    "to an empty string, and explain the mismatch in reason. "
                    "Returning no recommendation is better than a weak match. "
                    "Return JSON matching this schema:\n" + json.dumps(schema)
            ),
        }],
        format=schema,
        options={"num_ctx": 4096, "temperature": 0},
    )

    choice = json.loads(response.message.content)
    if not isinstance(choice, dict) or set(choice) != {"url", "title", "reason"}:
        raise ValueError("Invalid recommendation structure.")
    if not all(isinstance(choice[key], str) for key in ("title", "reason")):
        raise ValueError("Title and reason must be strings.")

    url = choice["url"]
    if url is not None and (not isinstance(url, str) or url not in read_urls):
        raise ValueError("Recommendation URL was not successfully read.")

    return choice
