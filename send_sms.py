import configparser
import sys
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# --- Configuration File ---
CONFIG_FILE = 'config.ini'

def create_config_file():
    """Creates a template config.ini file if it doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Creating default '{CONFIG_FILE}' file...")
        config = configparser.ConfigParser()
        config['Twilio'] = {
            'ACCOUNT_SID': 'PASTE_YOUR_SID_HERE',
            'AUTH_TOKEN': 'PASTE_YOUR_TOKEN_HERE',
            'TWILIO_NUMBER': 'PASTE_YOUR_TWILIO_NUMBER_HERE'
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print(f"✅ '{CONFIG_FILE}' created. Please edit it with your Twilio credentials.")
        sys.exit(0)

def read_config():
    """Reads and validates the configuration from config.ini."""
    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found.", file=sys.stderr)
        create_config_file()
    
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
        print("Please make sure your config file has ACCOUNT_SID, AUTH_TOKEN, and TWILIO_NUMBER.", file=sys.stderr)
        sys.exit(1)

def send_message(account_sid, auth_token, twilio_number, recipient_number, message_body):
    """
    Sends an SMS message using Twilio credentials.
    """
    # 1. Basic check on the recipient number
    if not recipient_number.startswith('+'):
        print(f"ERROR: Recipient number '{recipient_number}' is invalid.", file=sys.stderr)
        print("It must be in E.164 format (e.g., +919360331390).", file=sys.stderr)
        sys.exit(1)

    print(f"Initializing Twilio client to send to {recipient_number}...")

    # 2. Initialize the Twilio client
    try:
        client = Client(account_sid, auth_token)
    except Exception as e:
        print(f"ERROR: Could not initialize Twilio client. Check credentials? {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Try to send the message
    try:
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,    # Your Twilio number
            to=recipient_number     # The verified recipient number
        )
        print("---")
        print("✅ SUCCESS! Message Sent.")
        print(f"Message SID (Receipt): {message.sid}")
        print("---")

    except TwilioRestException as e:
        print("---", file=sys.stderr)
        print(f"❌ ERROR: Message failed to send.", file=sys.stderr)
        print(f"Twilio Error {e.code}: {e.msg}", file=sys.stderr)
        if e.code == 21614:
             print("INFO: This error (21614) often means you are using a Trial Account and", file=sys.stderr)
             print(f"the recipient number '{recipient_number}' is not verified in your Twilio console.", file=sys.stderr)
        print("---", file=sys.stderr)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)

# ===============================================
# --- MAIN EXECUTION: CONFIGURE YOUR TEST HERE ---
# ===============================================
if __name__ == "__main__":
    
    # 1. SET YOUR RECIPIENT'S PHONE NUMBER
    #    (Must be a number you have verified in your Twilio console)
    your_verified_number = "+919360331390"  # <-- CHANGE THIS

    # 2. SET YOUR MESSAGE
    alert_message = "Venv test. will send the values soon"
    
    # --- --- --- --- --- --- --- --- --- --- --- ---
    
    # Check for config file and read it
    create_config_file() # Will only run if the file is missing
    SID, TOKEN, TWILIO_NUM = read_config()
    
    # 3. SEND THE MESSAGE
    send_message(SID, TOKEN, TWILIO_NUM, your_verified_number, alert_message)

