from unittest.mock import MagicMock, patch
from agent.memory import ConversationStore
from langchain_core.messages import HumanMessage, AIMessage


def _make_store():
    with patch("agent.memory.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        store = ConversationStore(supabase_url="https://test.supabase.co", supabase_key="test-key")
        store._client = mock_client
    return store


def _mock_select(data):
    mock = MagicMock()
    mock.data = data
    chain = MagicMock()
    chain.execute.return_value = mock
    return chain


def test_empty_history_returns_empty_list():
    store = _make_store()
    store._client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
    assert store.get_history("contact_new") == []


def test_save_and_load_messages():
    store = _make_store()
    store._client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {"role": "human", "content": "Hello!"},
        {"role": "ai", "content": "Hi there!"},
    ]
    history = store.get_history("contact1")
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)
    assert history[0].content == "Hello!"
    assert history[1].content == "Hi there!"


def test_save_message_calls_insert():
    store = _make_store()
    store.save_message("contact1", "human", "Hello!")
    store._client.table.assert_called_with("messages")
    store._client.table.return_value.insert.assert_called_once()


def test_save_lead_context():
    store = _make_store()
    store._client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"context": {"score": 85, "lead_type": "hot"}}
    ]
    store.save_context("contact1", {"score": 85, "lead_type": "hot"})
    loaded = store.get_context("contact1")
    assert loaded["score"] == 85
    assert loaded["lead_type"] == "hot"


def test_save_opportunity_id():
    store = _make_store()
    store._client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"opportunity_id": "opp123"}
    ]
    store.save_opportunity_id("contact1", "opp123")
    assert store.get_opportunity_id("contact1") == "opp123"


def test_get_opportunity_id_returns_none_if_missing():
    store = _make_store()
    store._client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    assert store.get_opportunity_id("contact_new") is None
