# AI-Powered Code Review Bot

A GitHub App that leverages Claude (or another LLM) to automatically review pull requests, providing actionable feedback on style, potential bugs, security issues, and performance.

## Features

- **Webhook endpoint** – receives `pull_request` events from GitHub.
- **LLM-powered review** – builds a prompt from the diff and calls the Claude API.
- **Review comments** – posts structured, markdown-formatted feedback as a PR review.
- **CLI tool** – run locally for debugging: `ai-review review <owner>/<repo>#<PR>`
- **Dockerized** – easy deployment via GitHub Actions or any CI.
- **Configurable** – tune focus areas (style, security, performance) via YAML.
- **Feedback loop** – users can react with 👍/👎 to improve future prompts.

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for a detailed component diagram and data flow.

## Getting Started

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/ai-code-reviewer.git
   cd ai-code-reviewer
   ```

2. **Install dependencies**
   ```bash
   # Python example
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export ANTHROPIC_API_KEY=your_claude_key
   export GH_APP_ID=your_github_app_id
   export GH_PRIVATE_KEY=path/to/private-key.pem
   ```

4. **Run locally**
   ```bash
   python -m app.webhook  # starts the FastAPI server
   # or
   ai-review review owner/repo#123
   ```

5. **Deploy**
   - Build the Docker image: `docker build -t ghcr.io/yourusername/ai-code-reviewer .`
   - Use the provided GitHub Action workflow (`.github/workflows/review.yml`) to deploy as a bot.

## License

MIT

---
*Built with Claude Code*