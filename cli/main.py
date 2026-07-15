#!/usr/bin/env python3
"""
CLI entry point for the AI code review bot.
Fetches a PR diff (or reads from file), builds a prompt, calls Claude API, and prints the review.
"""

import argparse
import os
import sys
import logging
from dotenv import load_dotenv
from github import Github
import anthropic

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to sys.path so we can import app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.prompt_builder import build_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_github_token():
    token = os.getenv("GH_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("GitHub token not found. Set GH_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN env var.")
        sys.exit(1)
    return token

def get_anthropic_key():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        logger.error("Anthropic API key not found. Set ANTHROPIC_API_KEY env var.")
        sys.exit(1)
    return key

def fetch_pr_diff(repo_full_name: str, pr_number: int) -> tuple[str, str, str]:
    """
    Fetches the pull request diff and returns (diff_text, file_path, language).
    For simplicity, we concatenate all file diffs and use the first file's language.
    In a more advanced version, we could review each file separately.
    """
    token = get_github_token()
    g = Github(token)
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

def main():
    parser = argparse.ArgumentParser(description="AI Code Review Bot")
    parser.add_argument("repo", help="Repository in format owner/name")
    parser.add_argument("pr", type=int, help="Pull request number")
    parser.add_argument(
        "--diff-file",
        help="Path to a diff file to use instead of fetching from GitHub (for testing)",
    )
    args = parser.parse_args()

    if args.diff_file:
        # Read diff from file
        logger.info(f"Reading diff from {args.diff_file}")
        try:
            with open(args.diff_file, "r", encoding="utf-8") as f:
                diff = f.read()
        except OSError as e:
            logger.error(f"Cannot read diff file: {e}")
            sys.exit(1)
        # For file input, we need to guess language from file extension or use default
        file_path = args.diff_file
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        lang_map = {
            "py": "Python", "js": "JavaScript", "ts": "TypeScript",
            "java": "Java", "go": "Go", "rs": "Rust",
            "cpp": "C++", "c": "C", "html": "HTML", "css": "CSS",
        }
        language = lang_map.get(ext, "unknown")
        logger.info(f"Using language '{language}' based on file extension.")
    else:
        logger.info(f"Fetching PR #{args.pr} from {args.repo}...")
        diff, file_path, language = fetch_pr_diff(args.repo, args.pr)

    if not diff.strip():
        print("No diff found or empty PR.")
        return

    logger.info(f"Building prompt for {language} file {file_path}...")
    prompt = build_prompt(
        diff=diff,
        file_path=file_path,
        language=language,
        focus_areas=["style", "potential bugs", "security", "performance"],
    )

    logger.info("Calling Claude API...")
    client = anthropic.Anthropic(api_key=get_anthropic_key())
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
        sys.exit(1)

    print("\n=== Code Review ===\n")
    print(review_text)
    print("\n==================\n")

if __name__ == "__main__":
    main()