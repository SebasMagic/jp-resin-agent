import json
import sqlite3
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class ConversationStore:
    def __init__(self, db_path: str = "conversations.db"):
        self._db = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lead_context (
                    contact_id TEXT PRIMARY KEY,
                    context_json TEXT NOT NULL,
                    opportunity_id TEXT
                )
            """)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_contact ON messages(contact_id)")

    def save_message(self, contact_id: str, role: str, content: str):
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                "INSERT INTO messages (contact_id, role, content) VALUES (?, ?, ?)",
                (contact_id, role, content),
            )

    def get_history(self, contact_id: str) -> list[BaseMessage]:
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE contact_id = ? ORDER BY id ASC",
                (contact_id,),
            ).fetchall()
        result = []
        for role, content in rows:
            if role == "human":
                result.append(HumanMessage(content=content))
            elif role == "ai":
                result.append(AIMessage(content=content))
            else:
                raise ValueError(f"Unknown message role in DB: {role!r}")
        return result

    def save_context(self, contact_id: str, context: dict):
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                """
                INSERT INTO lead_context (contact_id, context_json)
                VALUES (?, ?)
                ON CONFLICT(contact_id) DO UPDATE SET context_json = excluded.context_json
                """,
                (contact_id, json.dumps(context)),
            )

    def get_context(self, contact_id: str) -> dict:
        with sqlite3.connect(self._db) as conn:
            row = conn.execute(
                "SELECT context_json FROM lead_context WHERE contact_id = ?",
                (contact_id,),
            ).fetchone()
        if not row:
            return {}
        return json.loads(row[0])

    def save_opportunity_id(self, contact_id: str, opportunity_id: str):
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                """
                INSERT INTO lead_context (contact_id, context_json, opportunity_id)
                VALUES (?, '{}', ?)
                ON CONFLICT(contact_id) DO UPDATE SET opportunity_id = excluded.opportunity_id
                """,
                (contact_id, opportunity_id),
            )

    def get_opportunity_id(self, contact_id: str) -> str | None:
        with sqlite3.connect(self._db) as conn:
            row = conn.execute(
                "SELECT opportunity_id FROM lead_context WHERE contact_id = ?",
                (contact_id,),
            ).fetchone()
        if not row:
            return None
        return row[0]
