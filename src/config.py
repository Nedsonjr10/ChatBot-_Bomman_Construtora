import os
from dotenv import load_dotenv

load_dotenv()

PORT         = int(os.getenv("PORT", 8000))
GATEWAY_URL  = os.getenv("GATEWAY_URL", "http://localhost:3000")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "127.0.0.1")
CLIENT_ID    = os.getenv("CLIENT_ID", "bomman")

raw_ignored    = os.getenv("IGNORED_NUMBERS", "")
IGNORED_NUMBERS = [n.strip() for n in raw_ignored.split(",") if n.strip()]

TEST_PREFIX = "#teste"
