from fastapi import FastAPI, Request, Header, HTTPException
import hashlib, hmac, os, json
import logging

from app.reviewer import review_pull_request, post_review_comment

app = FastAPI()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
logger = logging.getLogger(__name__)

@app.post("/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    body = await request.body()
    if WEBHOOK_SECRET:
        mac = hmac.new(WEBHOOK_SECRET.encode(), msg=body, digestmod=hashlib.sha256)
        expected = "sha256=" + mac.hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256 or ""):
            raise HTTPException(status_code=401, detail="Invalid signature")
    payload = json.loads(body)
    # Check if it's a pull request event and the action is one we care about
    if payload.get("action") in ["opened", "synchronize", "reopened"] and "pull_request" in payload:
        pr = payload["pull_request"]
        repo = payload["repository"]
        repo_full_name = repo["full_name"]
        pr_number = pr["number"]
        logger.info(f"Processing PR #{pr_number} from {repo_full_name} (action: {payload['action']})")
        try:
            # Review the pull request
            review_text = review_pull_request(repo_full_name, pr_number)
            # Post the review as a comment
            post_review_comment(repo_full_name, pr_number, review_text, os.getenv("GH_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN"))
            logger.info(f"Review posted for PR #{pr_number}")
        except Exception as e:
            logger.error(f"Error processing PR #{pr_number}: {e}")
            # We still return a 200 to avoid GitHub retries, but log the error
            # In a production system, you might want to handle this differently
            pass
    else:
        logger.info(f"Ignoring event: {payload.get('action')} for {payload.get('pull_request', {}).get('number') if 'pull_request' in payload else 'N/A'}")
    return {"status": "processed"}