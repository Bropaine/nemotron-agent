# Nemotron Agent

A local AI agent runtime built on an Ollama-hosted NVIDIA Nemotron model.
No cloud APIs and no keys: the agent runs entirely against a model served
from your own machine (`http://localhost:11434`).

## What it does

- **Skill system** — capabilities are defined as markdown files under
  `skills/` and loaded at runtime (`skill_loader.py`), with dynamic
  selection of the right skill for a request (`skill_selector.py`).
- **Web discovery** — bundled `web_discovery` skill backed by web search
  (`web_search.py`) and page reading (`web_reader.py`) tools.
- **Summarization** — bundled `summarize_text` skill.
- **Discovery app** — a StumbleUpon-style
  recommendation workflow: the agent surfaces web content as cards in a
  Flask UI, you rate with like/dislike plus reasons and notes, and a
  bounded recommendation engine learns from your ratings. Discovery
  history is stored locally in SQLite and is not tracked in git.

## Layout

- `main.py` — agent entry point (Ollama client, skill loop)
- `skill_loader.py` / `skill_selector.py` — skill loading and selection
- `web_search.py` / `web_reader.py` — web tools
- `skills/` — markdown skill definitions
- `agent.py`, `web_app.py`, `discovery_store.py`, `recommendation.py`
  — discovery agent, Flask app, local store,
  recommendation logic
- `tests/` — unit tests for skill selection, web reading, search
  filtering, ratings, and recommendation relevance

## Requirements

- Python 3
- A local [Ollama](https://ollama.com) instance serving a Nemotron model
  on `localhost:11434`

## Running

```bash
pip install -r requirements.txt
python main.py
