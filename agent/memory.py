from supabase import create_client, Client
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class ConversationStore:
    def __init__(self, supabase_url: str, supabase_key: str):
        self._client: Client = create_client(supabase_url, supabase_key)

    def save_message(self, contact_id: str, role: str, content: str):
        self._client.table("messages").insert({
            "contact_id": contact_id,
            "role": role,
            "content": content,
        }).execute()

    def get_history(self, contact_id: str) -> list[BaseMessage]:
        result = self._client.table("messages").select("role,content").eq("contact_id", contact_id).order("id").execute()
        messages = []
        for row in result.data:
            role = row["role"]
            content = row["content"]
            if role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))
            else:
                raise ValueError(f"Unknown message role: {role!r}")
        return messages

    def save_context(self, contact_id: str, context: dict):
        self._client.table("lead_context").upsert({
            "contact_id": contact_id,
            "context": context,
        }).execute()

    def get_context(self, contact_id: str) -> dict:
        result = self._client.table("lead_context").select("context").eq("contact_id", contact_id).execute()
        if result.data:
            return result.data[0]["context"]
        return {}

    def save_opportunity_id(self, contact_id: str, opportunity_id: str):
        self._client.table("lead_context").update({
            "opportunity_id": opportunity_id,
        }).eq("contact_id", contact_id).execute()

    def get_opportunity_id(self, contact_id: str) -> str | None:
        result = self._client.table("lead_context").select("opportunity_id").eq("contact_id", contact_id).execute()
        if result.data:
            return result.data[0].get("opportunity_id")
        return None
