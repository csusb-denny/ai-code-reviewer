# Architecture Overview

The AI Code Review Bot consists of several loosely‑coupled components that can be run independently or together via Docker.

## Components

1. **Webhook Service** (`app/webhook.py`)
   - Exposes a `/webhook` endpoint (FastAPI/Express).
   - Verifies GitHub signature, extracts `pull_request` payload.
   - Retrieves the pull request diff via the GitHub API.
   - Delegates diff to the **LLM Service**.
   - Posts the LLM’s review comments back as a PR review.

2. **LLM Service** (`app/llm_client.py`)
   - Thin wrapper around the Anthropic Claude SDK (or OpenAI, etc.).
   - Handles prompt templating, temperature settings, token limits.
   - Returns markdown formatted review comments.

3. **Prompt Builder** (`app/prompt_builder.py`)
   - Constructs the prompt sent to the LLM.
   - Parameters: target language, focus areas (style, security, performance), diff, optional file context.
   - Returns a single string prompt.

4. **CLI Interface** (`cli/__main__.py` or `ai-review` entrypoint)
   - Reuses the same core logic as the webhook.
   - Accepts `--repo` and `--pr` (or local path) to fetch diff and run review.
   - Prints comments to stdout or optionally posts via GitHub API calls.

5. **Configuration** (`config.yaml`)
   - Lists enabled review categories.
   - Sets temperature, max tokens, model name.
   - Optional paths to custom prompt templates.

6. **Dockerfile**
   - Base: `python:3.11-slim` (or `node:20-slim` for TS version).
   - Installs dependencies, copies source, sets entrypoint to launch webhook or CLI.
   - Exposes port 8080 for webhook.

7. **GitHub Action** (`.github/workflows/review.yml`)
   - Triggers on `pull_request` events.
   - Checks out the repo, builds/pushes Docker image (or uses pre‑built).
   - Runs the container with necessary secrets (`ANTHROPIC_API_KEY`, `GITHUB_TOKEN`).

## Data Flow

```
GitHub (PR event) --> Webhook Service --> GitHub API (fetch diff)
                                 |
                                 v
                          Prompt Builder --> LLM Service (Claude)
                                 |
                                 v
                      Webhook Service --> GitHub API (create review comment)
```

## Extensibility

- **Multiple LLMs**: swap the `llm_client` implementation.
- **Additional analysis**: plug in static analysis tools (e.g., Bandit, ESLint) and merge their findings.
- **Custom channels**: add Slack/Discord notifier by reusing the LLM output.

## Diagram (textual)

```
+-------------------+       +---------------------+       +-------------------+
|   GitHub Webhook  | --->  |   Webhook Service   | --->  |   GitHub API      |
+-------------------+       +---------------------+       +-------------------+
          ^                         |   ^                         |
          |                         |   |                         |
          |                         v   |                         v
          |               +-------------------+        +-------------------+
          |               |  Prompt Builder   |        |   LLM Service     |
          |               +-------------------+        +-------------------+
          |                         |                         |
          |                         v                         v
          |               +-------------------+        +-------------------+
          +---------------|   Review Output   |<-------|   Post Comment    |
                          +-------------------+        +-------------------+
```

## Development Tips

- Run tests with `pytest` (`npm test` for TS).
- Use `pre-commit` hooks for linting.
- When adding a new language, extend the prompt builder with language‑specific hints.

---