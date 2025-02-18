from fastapi import FastAPI, Request
from typing import Dict, Any
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # This ensures logs go to Vercel's console
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="My FastAPI App",
    description="A sample FastAPI application",
    version="1.0.0"
)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    # Get the raw JSON data from the request
    data: Dict[Any, Any] = await request.json()
    
    # Log the incoming webhook data
    logger.info(f"Received webhook data: {data}")
    
    # Extract the message status updates
    try:
        entries = data.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                if change.get("field") == "messages":
                    messages = change.get("value", {}).get("messages", [])
                    statuses = change.get("value", {}).get("statuses", [])
                    
                    # Process message statuses
                    for status in statuses:
                        status_type = status.get("status")  # sent, delivered, read, failed
                        message_id = status.get("id")
                        timestamp = status.get("timestamp")
                        
                        logger.info(f"Message {message_id} status: {status_type} at {timestamp}")
                        
                        # Here you can add your own logic to handle different status types
                        # For example, update your database, send notifications, etc.
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

# WhatsApp requires GET verification for the webhook
@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    # Get query parameters
    params = request.query_params
    logger.info(f"Verification request received with params: {params}")
    
    # WhatsApp sends a verification token that you need to echo back
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    # Replace 'your_verify_token' with your actual verify token
    verify_token = "your_verify_token"
    
    if mode and token:
        if mode == "subscribe" and token == verify_token:
            if challenge:
                logger.info(f"Webhook verified successfully. Challenge: {challenge}")
                return int(challenge)
            return "OK"
    
    logger.warning("Invalid verification token received")
    return {"status": "error", "message": "Invalid verification token"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
