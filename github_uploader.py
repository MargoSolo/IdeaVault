"""
github_uploader.py
Creates a new Markdown file in the configured GitHub repository.
"""
import base64
import os
from datetime import datetime, timezone, timedelta

from github import Github
from dotenv import load_dotenv

load_dotenv()

_gh = Github(os.environ["GITHUB_TOKEN"])
_repo_name = os.environ["GITHUB_REPO"]


def _slugify(title: str) -> str:
    """Convert a title to a URL/filename-safe slug."""
    import re
    # Replace spaces and special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:60]  # cap length


def _build_frontmatter(data: dict, created_at: str) -> str:
    tags_yaml = "\n".join(f'  - "{t}"' for t in data.get("tags", []))
    return (
        "---\n"
        f'title: "{data["title"]}"\n'
        f"date: {created_at}\n"
        f"tags:\n{tags_yaml}\n"
        f'folder: "{data["folder"]}"\n'
        "---\n\n"
    )


def upload_note(data: dict) -> str:
    """
    Create a Markdown file in GitHub.

    Args:
        data: dict with keys folder, title, tags, body

    Returns:
        The HTML URL of the created file.
    """
    repo = _gh.get_repo(_repo_name)

    # Use local Moscow time (UTC+3) for the date stamp
    moscow_tz = timezone(timedelta(hours=3))
    now = datetime.now(moscow_tz)
    date_str = now.strftime("%Y-%m-%d")
    created_at = now.strftime("%Y-%m-%dT%H:%M:%S%z")

    slug = _slugify(data["title"])
    filename = f"{date_str}-{slug}.md"
    folder = data.get("folder", "00_Inbox")
    file_path = f"{folder}/{filename}"

    frontmatter = _build_frontmatter(data, created_at)
    content = frontmatter + data.get("body", "")

    result = repo.create_file(
        path=file_path,
        message=f"✨ New note: {data['title']}",
        content=content,
        branch="main",
    )

    return result["content"].html_url
