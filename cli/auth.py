import base64
import hashlib
import secrets
import urllib.parse
import webbrowser
import socketserver
import http.server
import requests
from config import CLIENT_ID, REDIRECT_URI, BACKEND_URL

authorization_code = None

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
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
            slef.wfile.write(b"Authorization failed")

def login_flow():
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

    #start local server to catch the redirect
    print("Waiting for browser authorization...")
    with socketserver.TCPServer(("localhost", 8080), CallbackHandler) as httpd:
        httpd.handle_request() # this blocks until Github redirects back to localhost:8080
    
    print(f"Captured code: {authorization_code}")
    print(f"code verifier: {code_verifier}")

    print("Exchaning code for access token")

    payload = {
        "code": authorization_code,
        "code_verifier": code_verifier
    }

    try:
        response = requests.post(f"{BACKEND_URL}/auth/github/exchange", json=payload)
        response.raise_for_status() # raises an error for bad status codes

        token_data = response.json()
        print("login successful")
        # TODO - later save this token data to a local file
        print(token_data)
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to authenticate with backend: {e}")
    