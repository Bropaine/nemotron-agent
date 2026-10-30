import json
from pathlib import Path
from ollama import Client
from skill_loader import build_skill_catalog, load_skill
from skill_selector import select_skill

project_dir = Path(__file__).resolve().parent
catalog = build_skill_catalog(project_dir / "skills")
client = Client(host="http://localhost:11434")

request = input("Task: ").strip()
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
                    "Preserve uncertainty: keep words such as may, considering, planned, and expected. Do not turn "
                    "tentative statements into definite outcomes."
                    + json.dumps(catalog)
            ),
        },
        {"role": "user", "content": request},
    ],
    options={"num_ctx": 4096},
)
selected_id = response.message.content.strip()

if selected_id == "NONE":
    print("No matching skill.")
elif selected_id not in catalog:
    print("Invalid skill selection:", selected_id)
else:
    print("Validated skill:", selected_id)
    selected_path = project_dir / "skills" / selected_id / "SKILL.md"
    selected_text = load_skill(selected_path)
    print(selected_text)
    answer = client.chat(
        model="nemotron-3-nano:30b",
        messages=[
            {
                "role": "system",
                "content": (

                        "Follow the selected skill below. "
                        "No tools are connected to this call. "
                        "If required input is missing, ask for it.\n\n"
                        + selected_text
                ),
            },
            {"role": "user", "content": request},
        ],
        options={"num_ctx": 4096},
    )
    print("Answer:", answer.message.content)
