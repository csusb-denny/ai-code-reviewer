#!/usr/bin/env python3
"""
CLI entry point for the AI code review bot.
"""

import argparse

def main():
    parser = argparse.ArgumentParser(description="AI Code Review Bot")
    parser.add_argument("repo", help="Repository in format owner/name")
    parser.add_argument("pr", type=int, help="Pull request number")
    args = parser.parse_args()
    print(f"Would review PR #{args.pr} in {args.repo}")

if __name__ == "__main__":
    main()