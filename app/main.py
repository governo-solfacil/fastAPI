from fastapi import FastAPI, Request
from typing import Dict, Any
import logging
import sys
from supabase import create_client
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # This ensures logs go to Vercel's console
)

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

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
    data: Dict[Any, Any] = await request.json()
    logger.info(f"Received webhook data: {data}")
    
    try:
        entries = data.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                if change.get("field") == "messages":
                    statuses = change.get("value", {}).get("statuses", [])
                    
                    # Process message statuses
                    for status in statuses:
                        message_id = status.get("id")
                        status_type = status.get("status")
                        
                        if not message_id:
                            continue
                            
                        # Update status only if message exists in our system
                        result = supabase.table("whatsapp_messages").update({
                            "status": status_type
                        }).eq("whatsapp_message_id", message_id).execute()
                        
                        if result.data:
                            logger.info(f"Updated status for message {message_id} to {status_type}")
                        else:
                            logger.info(f"Ignored status update for unknown message {message_id}")
        
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
    verify_token = "2123"
    
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
