"""
Reviewer module for the AI code review bot.
Contains functions to fetch PR diffs, build prompts, call the LLM, and post review comments.
"""

import os
import logging
from typing import Optional
import anthropic
from github import Github

from .prompt_builder import build_prompt

logger = logging.getLogger(__name__)

def get_github_token() -> str:
    """Get GitHub token from environment variables."""
    token = os.getenv("GH_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("GitHub token not found. Set GH_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN env var.")
        raise ValueError("GitHub token not found")
    return token

def get_anthropic_key() -> str:
    """Get Anthropic API key from environment variables."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        logger.error("Anthropic API key not found. Set ANTHROPIC_API_KEY env var.")
        raise ValueError("Anthropic API key not found")
    return key

def fetch_pr_diff(repo_full_name: str, pr_number: int, github_token: str) -> tuple[str, str, str]:
    """
    Fetches the pull request diff and returns (diff_text, file_path, language).
    For simplicity, we concatenate all file diffs and use the first file's language.
    In a more advanced version, we could review each file separately.
    """
    g = Github(github_token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    # Get all files in the PR
    files = list(pr.get_files())
    if not files:
        logger.warning("No files found in PR.")
        return "", "", "unknown"

    diffs = []
    file_path = files[0].filename
    language = None
    for f in files:
        if f.patch:
            diffs.append(f.patch)
        # Determine language from first file
        if language is None and f.filename:
            ext = f.filename.split('.')[-1].lower() if '.' in f.filename else ''
            lang_map = {
                "py": "Python", "js": "JavaScript", "ts": "TypeScript",
                "java": "Java", "go": "Go", "rs": "Rust",
                "cpp": "C++", "c": "C", "html": "HTML", "css": "CSS",
            }
            language = lang_map.get(ext, "unknown")
    diff_text = "\n\n".join(diffs)
    if language is None:
        language = "unknown"
    return diff_text, file_path, language

def get_review_from_claude(prompt: str, anthropic_key: str) -> str:
    """
    Calls the Claude API to get a code review.
    Returns the review text.
    """
    client = anthropic.Anthropic(api_key=anthropic_key)
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # adjust as needed
            max_tokens=1024,
            temperature=0.0,
            system="You are an expert code reviewer.",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        # Extract text from content blocks
        review_text = ""
        for block in message.content:
            if getattr(block, 'type', None) == "text":
                review_text += block.text
        if not review_text:
            # fallback
            review_text = str(message)
            # If content is empty, maybe the model refused?
            fallback = getattr(message, 'content', [])
            if fallback and isinstance(fallback, list):
                for blk in fallback:
                    if hasattr(blk, 'text'):
                        review_text += blk.text
        if not review_text:
            review_text = "[No content returned from API]"
    except Exception as e:
        logger.error(f"Error calling Claude API: {e}")
        raise
    return review_text

def review_diff(diff: str, file_path: str, language: str,
                focus_areas: Optional[list[str]] = None,
                anthropic_key: str = None) -> str:
    """
    Reviews a given diff by building a prompt and calling Claude.
    Returns the review text.
    """
    if focus_areas is None:
        focus_areas = ["style", "potential bugs", "security", "performance"]
    if anthropic_key is None:
        anthropic_key = get_anthropic_key()

    prompt = build_prompt(
        diff=diff,
        file_path=file_path,
        language=language,
        focus_areas=focus_areas,
    )
    return get_review_from_claude(prompt, anthropic_key)

def post_review_comment(repo_full_name: str, pr_number: int, review_text: str, github_token: str) -> None:
    """
    Posts the review as a comment on the pull request.
    """
    g = Github(github_token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    # Create a review comment (as a general comment on the PR, not inline)
    # For a more sophisticated review, we could create a review with comments, but for simplicity:
    # We'll create a single comment with the review.
    # Note: GitHub API allows creating a review with comments, but that's more complex.
    # For now, we'll create a regular issue comment.
    issue = repo.get_issue(number=pr_number)
    issue.create_comment(f"## AI Code Review\n\n{review_text}")
    logger.info(f"Posted review comment on PR #{pr_number}")

def review_pull_request(repo_full_name: str, pr_number: int,
                       focus_areas: Optional[list[str]] = None) -> str:
    """
    Main function to review a pull request.
    Fetches the diff, builds prompt, calls Claude, and returns the review text.
    Does not post the comment (caller can decide to post or not).
    """
    if focus_areas is None:
        focus_areas = ["style", "potential bugs", "security", "performance"]

    github_token = get_github_token()
    anthropic_key = get_anthropic_key()

    logger.info(f"Fetching PR #{pr_number} from {repo_full_name}...")
    diff, file_path, language = fetch_pr_diff(repo_full_name, pr_number, github_token)

    if not diff.strip():
        logger.warning("No diff found or empty PR.")
        return "No changes found in the pull request."

    logger.info(f"Building prompt for {language} file {file_path}...")
    review_text = review_diff(diff, file_path, language, focus_areas, anthropic_key)

    return review_text