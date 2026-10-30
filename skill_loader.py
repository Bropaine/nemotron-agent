from pathlib import Path


def load_skill(skill_path: Path) -> str:
    """Read a skill's instructions from a Markdown file."""
    return skill_path.read_text(encoding="utf-8")


def discover_skills(skills_dir: Path) -> list[Path]:
    """Find SKILL.md files one folder below the skills directory."""
    return sorted(skills_dir.glob("*/SKILL.md"))


def read_skill_metadata(skill_path: Path) -> dict[str, str]:
    metadata = {}

    for line in load_skill(skill_path).splitlines():
        if line.startswith("Name:"):
            metadata["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Description:"):
            metadata["description"] = line.split(":", 1)[1].strip()
        elif line.strip() == "Instructions:":
            break

    return metadata


def build_skill_catalog(skills_dir: Path) -> dict[str, dict[str, str]]:
    catalog = {}

    for skill_path in discover_skills(skills_dir):
        skill_id = skill_path.parent.name
        catalog[skill_id] = read_skill_metadata(skill_path)

    return catalog