# tests/test_memory.py
import os
import pytest
from agent.memory import ConversationStore
from langchain_core.messages import HumanMessage, AIMessage


@pytest.fixture
def store(tmp_path):
    db = str(tmp_path / "test.db")
    s = ConversationStore(db_path=db)
    yield s
    if os.path.exists(db):
        os.remove(db)


def test_empty_history_returns_empty_list(store):
    history = store.get_history("contact_new")
    assert history == []


def test_save_and_load_messages(store):
    store.save_message("contact1", "human", "Hello!")
    store.save_message("contact1", "ai", "Hi there!")
    history = store.get_history("contact1")
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)
    assert history[0].content == "Hello!"
    assert history[1].content == "Hi there!"


def test_separate_contacts_have_separate_history(store):
    store.save_message("contact_a", "human", "I'm contact A")
    store.save_message("contact_b", "human", "I'm contact B")
    a_history = store.get_history("contact_a")
    b_history = store.get_history("contact_b")
    assert len(a_history) == 1
    assert len(b_history) == 1
    assert a_history[0].content == "I'm contact A"
    assert b_history[0].content == "I'm contact B"


def test_save_lead_context(store):
    context = {"score": 85, "lead_type": "hot", "state": "Georgia"}
    store.save_context("contact1", context)
    loaded = store.get_context("contact1")
    assert loaded["score"] == 85
    assert loaded["lead_type"] == "hot"


def test_save_opportunity_id(store):
    store.save_opportunity_id("contact1", "opp123")
    assert store.get_opportunity_id("contact1") == "opp123"


def test_get_opportunity_id_returns_none_if_missing(store):
    assert store.get_opportunity_id("contact_new") is None
