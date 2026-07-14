#!/usr/bin/env python3
"""
CLI entry point for the AI code review bot (module execution).
"""

import sys
from .prompt_builder import build_prompt

def main() -> None:
    # Sample diff and file info for demonstration
    sample_diff = '''def hello_world():
    print("Hello, World!")
    return 42
'''
    sample_file = "example.py"
    sample_language = "Python"
    sample_focus = ["style", "potential bugs"]

    prompt = build_prompt(
        diff=sample_diff,
        file_path=sample_file,
        language=sample_language,
        focus_areas=sample_focus,
    )
    # Use UTF-8 to avoid encoding issues on Windows console
    buffer = prompt.encode('utf-8')
    sys.stdout.buffer.write(buffer)
    sys.stdout.buffer.write(b'\n')

if __name__ == "__main__":
    main()