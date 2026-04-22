import os

# Must be set before any import of config.py (pydantic-settings reads at instantiation)
os.environ.setdefault("GHL_PIT_TOKEN", "test-token")
os.environ.setdefault("GHL_LOCATION_ID", "loc123")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("GOOGLE_SHEETS_CSV_URL", "https://example.com/sheet.csv")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("WEBHOOK_SECRET", "changeme")
