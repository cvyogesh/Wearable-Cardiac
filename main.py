import configparser
import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import uvicorn

# --- Configuration ---
CONFIG_FILE = 'config.ini'

# --- 1. Pydantic Model (Data Validation) ---
# This tells FastAPI what the incoming JSON should look like.
# It automatically validates the 'message' field.
class AlertRequest(BaseModel):
    message: str

# --- 2. Twilio Helper Functions (Unchanged) ---
def read_config():
    """Reads and validates the configuration from config.ini."""
    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found.", file=sys.stderr)
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    
    try:
        twilio_config = config['Twilio']
        account_sid = twilio_config['ACCOUNT_SID']
        auth_token = twilio_config['AUTH_TOKEN']
        twilio_number = twilio_config['TWILIO_NUMBER']
        
        if 'PASTE_YOUR_SID_HERE' in account_sid:
            print("ERROR: Please open 'config.ini' and fill in your Twilio credentials.", file=sys.stderr)
            sys.exit(1)
            
        return account_sid, auth_token, twilio_number
        
    except KeyError as e:
        print(f"ERROR: Missing key {e} in '{CONFIG_FILE}'.", file=sys.stderr)
        sys.exit(1)

def send_message(account_sid, auth_token, twilio_number, recipient_number, message_body):
    """
    Sends an SMS message using Twilio.
    Returns (True, message_sid) on success, (False, error_message) on failure.
    """
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=recipient_number
        )
        print(f"Successfully sent message: {message.sid}")
        return True, message.sid
    except TwilioRestException as e:
        print(f"Twilio error: {e}", file=sys.stderr)
        return False, str(e)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False, str(e)

# --- 3. Initialize FastAPI App ---
app = FastAPI()

# --- 4. Add CORS Middleware ---
# This allows your HTML file (from a 'file://' or other origin)
# to talk to your server (at 'http://127.0.0.1:8000')
origins = ["*"]  # Allow all origins for this demo

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (POST, GET, etc.)
    allow_headers=["*"], # Allow all headers
)

# --- 5. Load Config on Startup ---
# This is more efficient. We read the config once when the server starts.
try:
    SID, TOKEN, TWILIO_NUM = read_config()
except SystemExit:
    sys.exit(1) # Exit if config is bad

# --- 6. Create the API Endpoint ---
@app.post("/send_alert")
def handle_alert(alert: AlertRequest):
    """
    This endpoint receives an alert and sends an SMS.
    'alert' is a pydantic model, so 'alert.message' is guaranteed to exist.
    """
    print("Received alert request from frontend...")
    
    try:
        doctor_number = "+919360331390" 
        
        # Call the synchronous send_message function.
        # FastAPI is smart and will run this in a threadpool
        # so it doesn't block the server.
        success, sid_or_error = send_message(SID, TOKEN, TWILIO_NUM, doctor_number, alert.message)
        
        if success:
            print("Alert sent successfully.")
            # FastAPI automatically converts this dict to JSON
            return {"status": "Alert sent", "sid": sid_or_error}
        else:
            print(f"Failed to send alert: {sid_or_error}")
            # Raise a proper HTTP error that the frontend can catch
            raise HTTPException(status_code=500, detail=f"Failed to send: {sid_or_error}")
    
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

# --- 7. Start the Server (if running this file directly) ---
if __name__ == "__main__":
    print("Starting FastAPI server with Uvicorn at http://127.0.0.1:8000")
    # --reload enables auto-reload when you save the file
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
