from flask import Flask, request, redirect
from evernote.api.client import EvernoteClient
import urllib.parse

# Initialize Flask app
app = Flask(__name__)

# Evernote API credentials (Replace these with your actual credentials)
CONSUMER_KEY = "integration-0008"
CONSUMER_SECRET = "924aa0548dc7b655e9efc9dc6ec23f5988497b737e476f5da913b5ec"

# Use Evernote's production or sandbox environment
USE_SANDBOX = False  # Set to True for testing

# Initialize Evernote client
client = EvernoteClient(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    sandbox=USE_SANDBOX
)

# Store request tokens (should be improved for multi-user apps)
request_tokens = {}

@app.route("/")
def home():
    """Step 1: Get Request Token and Redirect to Evernote"""
    callback_url = "http://127.0.0.1:5000/callback"
    
    try:
        # Get request token
        request_token = client.get_request_token(callback_url)
        
        # Debugging: Print raw request_token and its type
        print(f"Raw request_token: {request_token}")
        print(f"Type of request_token: {type(request_token)}")

        # Check what kind of response we got (dictionary or string)
        if isinstance(request_token, dict):
            # If it's a dictionary, use it directly
            oauth_token = request_token.get('oauth_token')
            oauth_token_secret = request_token.get('oauth_token_secret')
            
            if not oauth_token:
                return "Error: OAuth token not found in response", 400
                
            # Store both tokens
            request_tokens[oauth_token] = request_token
        elif isinstance(request_token, str):
            # If it's a string, try to parse it as a query string
            parsed_token = dict(urllib.parse.parse_qsl(request_token))
            print(f"Parsed token: {parsed_token}")
            
            oauth_token = parsed_token.get('oauth_token')
            oauth_token_secret = parsed_token.get('oauth_token_secret')
            
            if not oauth_token:
                return "Error: OAuth token not found in parsed response", 400
                
            # Store both parsed tokens
            request_tokens[oauth_token] = parsed_token
        else:
            return f"Unexpected request_token type: {type(request_token)}", 400

        print(f"Stored request token in request_tokens: {request_tokens}")

        # Redirect user to Evernote authorization URL
        # The client.get_authorize_url() expects the entire request_token dictionary, not just the oauth_token string
        if isinstance(request_token, dict):
            auth_url = client.get_authorize_url(request_token)
        else:
            # If we're working with a parsed string, recreate the dictionary
            auth_url = client.get_authorize_url(parsed_token)
        
        return redirect(auth_url)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error in / route: {e}", 400

@app.route("/callback")
def oauth_callback():
    """Step 2: Handle OAuth Callback and Exchange for Access Token"""
    oauth_token = request.args.get("oauth_token")
    oauth_verifier = request.args.get("oauth_verifier")

    print(f"Received oauth_token: {oauth_token}")
    print(f"Received oauth_verifier: {oauth_verifier}")
    
    if oauth_token and oauth_verifier:
        # Debug: print request_tokens to verify its contents
        print(f"request_tokens in callback: {request_tokens}")

        # Retrieve request token using oauth_token as key
        request_token = request_tokens.get(oauth_token)
        print(f"Retrieved request_token: {request_token}")

        if request_token:
            try:
                # Get the token and secret, handling both dictionary and string cases
                if isinstance(request_token, dict):
                    token = request_token.get('oauth_token')
                    token_secret = request_token.get('oauth_token_secret')
                else:
                    # If we somehow got a string at this point
                    parsed = dict(urllib.parse.parse_qsl(request_token))
                    token = parsed.get('oauth_token')
                    token_secret = parsed.get('oauth_token_secret')
                
                if not token or not token_secret:
                    return "Error: Missing token or token secret", 400
                
                # Exchange the request token for an access token
                access_token = client.get_access_token(
                    token,
                    token_secret,
                    oauth_verifier
                )

                return f"Access Token: {access_token}<br>Now you can use it to interact with the Evernote API."
            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"Error exchanging request token for access token: {e}", 400
        else:
            return "Error: Invalid request token.", 400
    return "OAuth failed: Missing OAuth parameters", 400

@app.route("/test_api")
def test_api():
    """Step 3: Use the Access Token to Make API Calls"""
    access_token = "your_access_token_here"  # Replace with your real access token
    authenticated_client = EvernoteClient(token=access_token, sandbox=USE_SANDBOX)
    note_store = authenticated_client.get_note_store()

    # Example: Fetch and list notebooks
    notebooks = note_store.listNotebooks()
    notebook_names = "<br>".join([notebook.name for notebook in notebooks])

    return f"Your Notebooks:<br>{notebook_names}"

if __name__ == "__main__":
    app.run(port=5000, debug=True)