from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
REDIRECT_URI = "http://localhost:8080/callback"
BACKEND_URL = "https://hng-projects.fastapicloud.dev"