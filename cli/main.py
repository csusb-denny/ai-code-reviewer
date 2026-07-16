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

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to sys.path so we can import app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.reviewer import review_pull_request, review_diff
from app.prompt_builder import build_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

        # Build prompt and call Claude via reviewer module
        logger.info(f"Building prompt for {language} file {file_path}...")
        review_text = review_diff(
            diff=diff,
            file_path=file_path,
            language=language,
            focus_areas=["style", "potential bugs", "security", "performance"],
        )
    else:
        logger.info(f"Fetching PR #{args.pr} from {args.repo}...")
        review_text = review_pull_request(
            repo_full_name=args.repo,
            pr_number=args.pr,
            focus_areas=["style", "potential bugs", "security", "performance"],
        )

    if not review_text.strip():
        print("No review generated.")
        return

    print("\n=== Code Review ===\n")
    print(review_text)
    print("\n==================\n")


if __name__ == "__main__":
    main()