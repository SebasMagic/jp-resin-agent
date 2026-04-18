import os

# Must be set before any import of config.py (pydantic-settings reads at instantiation)
os.environ.setdefault("GHL_PIT_TOKEN", "test-token")
os.environ.setdefault("GHL_LOCATION_ID", "loc123")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("GOOGLE_SHEETS_ID", "sheet123")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_JSON", '{"type":"service_account","project_id":"test","private_key_id":"x","private_key":"x","client_email":"x@x.iam.gserviceaccount.com","client_id":"1","auth_uri":"https://x","token_uri":"https://x"}')
os.environ.setdefault("WEBHOOK_SECRET", "changeme")
os.environ.setdefault("DB_PATH", ":memory:")
