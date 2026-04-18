from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    GHL_PIT_TOKEN: str
    GHL_LOCATION_ID: str
    GHL_PIPELINE_ID: str = ""
    GHL_STAGE_NEW_LEAD: str = ""
    GHL_STAGE_HOT: str = ""
    GHL_STAGE_MID: str = ""
    GHL_STAGE_COLD: str = ""
    GHL_STAGE_IN_CONVERSATION: str = ""
    GHL_STAGE_CALL_SCHEDULED: str = ""
    GHL_STAGE_ENROLLED: str = ""
    GHL_STAGE_NOT_INTERESTED: str = ""

    GHL_FIELD_EXPERIENCE: str = ""
    GHL_FIELD_GOAL: str = ""
    GHL_FIELD_INVESTMENT: str = ""

    GHL_WORKFLOW_NURTURE_ROI: str = ""
    GHL_WORKFLOW_NURTURE_CLASS_INFO: str = ""
    GHL_WORKFLOW_FOLLOWUP_HOT: str = ""
    GHL_WORKFLOW_FOLLOWUP_MID: str = ""
    GHL_WORKFLOW_FOLLOWUP_COLD: str = ""

    DEEPSEEK_API_KEY: str

    GOOGLE_SHEETS_ID: str
    GOOGLE_SERVICE_ACCOUNT_JSON: str

    WEBHOOK_SECRET: str = "changeme"

    DB_PATH: str = "conversations.db"


settings = Settings()
