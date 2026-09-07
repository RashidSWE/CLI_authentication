import base64
import hashlib
import secrets
import urllib.parse
import webbrowser
import socketserver
import http.server
import requests
from config import CLIENT_ID, REDIRECT_URI, BACKEND_URL
import json
import os

authorization_code = None

def save_credentials(token_data):
    """ Save credentials in a folder (hidden) """
    config_dir = os.path.expanduser("~/.insighta")
    os.makedirs(config_dir, exist_ok=True)
    creds_path = os.path.join(config_dir, "credentials.json")
    with open(creds_path, "w") as f:
        import json
        json.dump(token_data, f)

    print(f"\n credentials securely saved to {creds_path}")


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """ OAuth callback handler to authorize code for login """
        global authorization_code

        #parse the url to finde the ?code=... parameter
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            authorization_code = params["code"][0]
            # send success message to the browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Login successful!</h1><p>Return to your terminal.</p></body></html>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed")

def load_credentials():
    """ load saved credentials from a local config file """
    creds_path = os.path.expanduser("~/.insighta/credentials.json")
    if not os.path.exists(creds_path):
        return None
    
    with open(creds_path, "r") as f:
        return json.load(f)

def whoami():
    """ Command that checks who is currently logged in by validating scored credentials"""
    creds = load_credentials()
    if not creds:
        print("Not logged in. Pleas run 'insighta login' First.")
        return
    
    access_token = creds.get("access_token")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    print("Fetching Profile")

    try:
        response = requests.get(f"{BACKEND_URL}/api/Profile/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Logged in as {data.get('username')}")
        else:
            print(f"Session expired or invalid: {response.text}")
            print("Try running Insighta login again to login.")
    
    except Exception as e:
        print(f"Failed to connect to backend: {e}")

def login_flow():
    """ OAuth login flow"""
    verifier_bytes = secrets.token_bytes(32)
    code_verifier =  base64.urlsafe_b64encode(verifier_bytes).decode('utf-8').rstrip('=')
    hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge  = base64.urlsafe_b64encode(hashed).decode('utf-8').rstrip('=')

    # Build url and open browser
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "read:user",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    auth_url = f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"
    webbrowser.open(auth_url)

    # start local server to catch the redirect
    print("Waiting for browser authorization...")
    with socketserver.TCPServer(("localhost", 8080), CallbackHandler) as httpd:
        httpd.handle_request()
    
    print(f"Captured code: {authorization_code}")

    print("Exchaning code for access token")

    payload = {
        "code": authorization_code,
        "code_verifier": code_verifier
    }

    try:
        response = requests.post(f"{BACKEND_URL}/auth/github/exchange", json=payload)
        if response.status_code != 200:
            print(f"\n backend rejected the exchange, Details:")
            print(response.json())
            return

        token_data = response.json()
        print("login successful")

        save_credentials(token_data)
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to authenticate with backend: {e}")
    