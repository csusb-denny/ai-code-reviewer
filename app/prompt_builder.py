# app/prompt_builder.py
from typing import List, Dict, Optional

def build_prompt(
    diff: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    focus_areas: Optional[List[str]] = None,
) -> str:
    """
    Return a ready‑to‑send prompt for the LLM.

    Parameters
    ----------
    diff: str
        The unified diff of the pull request (or a single file diff).
    file_path: str | None
        Optional path of the file the diff belongs to – useful for language detection.
    language: str | None
        Programming language (e.g. "Python", "JavaScript"). If omitted we try to infer.
    focus_areas: list[str] | None
        e.g. ["style", "security", "performance"]. Defaults to a sensible set.
    """
    if focus_areas is None:
        focus_areas = ["style", "potential bugs", "security", "performance"]

    # Very simple language detection – you can replace with a proper library later.
    if language is None and file_path:
        ext = file_path.split(".")[-1].lower()
        lang_map = {
            "py": "Python",
            "js": "JavaScript",
            "ts": "TypeScript",
            "java": "Java",
            "go": "Go",
            "rs": "Rust",
        }
        language = lang_map.get(ext, "unknown")

    focus_str = ", ".join(focus_areas)

    prompt = f"""You are an expert {language} code reviewer.
Review the following diff for issues related to {focus_str}.
Provide concise, actionable feedback in GitHub‑flavored Markdown.
If there are no issues, respond exactly with "No issues found."

<diff>
{diff}
</diff>
"""
    return prompt