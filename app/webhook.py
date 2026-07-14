from fastapi import FastAPI, Request, Header, HTTPException
import hashlib, hmac, os, json
import httpx

app = FastAPI()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

@app.post("/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    body = await request.body()
    if WEBHOOK_SECRET:
        mac = hmac.new(WEBHOOK_SECRET.encode(), msg=body, digestmod=hashlib.sha256)
        expected = "sha256=" + mac.hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256 or ""):
            raise HTTPException(status_code=401, detail="Invalid signature")
    payload = json.loads(body)
    # For demo just echo
    return {"status": "received", "action": payload.get("action")}