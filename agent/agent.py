from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from config import settings
from models.lead import LeadType, ClassInfo
from services.ghl import GHLClient
from services.sheets import SheetsClient
from agent.memory import ConversationStore
from agent.tools import build_tools
from agent.prompts import build_system_prompt


def create_agent(
    contact_id: str,
    lead_type: LeadType,
    lead_context: dict,
    classes: list[ClassInfo],
    ghl: GHLClient,
    sheets: SheetsClient,
    store: ConversationStore,
) -> tuple:
    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_base="https://api.deepseek.com/v1",
        openai_api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.7,
    )

    tools = build_tools(
        contact_id=contact_id,
        ghl=ghl,
        sheets=sheets,
        store=store,
        settings=settings,
        lead_channel=lead_context.get("channel", "SMS"),
    )

    system_prompt = build_system_prompt(lead_type, lead_context, classes)
    history = store.get_history(contact_id)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        max_execution_time=30,
    )
    return executor, history


def run_agent(
    contact_id: str,
    human_message: str,
    lead_type: LeadType,
    lead_context: dict,
    classes: list[ClassInfo],
    ghl: GHLClient,
    sheets: SheetsClient,
    store: ConversationStore,
) -> str:
    executor, history = create_agent(
        contact_id=contact_id,
        lead_type=lead_type,
        lead_context=lead_context,
        classes=classes,
        ghl=ghl,
        sheets=sheets,
        store=store,
    )
    store.save_message(contact_id, "human", human_message)
    try:
        result = executor.invoke({
            "input": human_message,
            "chat_history": history,
        })
        output = result.get("output") or ""
    except Exception as exc:
        store.save_message(contact_id, "ai", f"[ERROR: agent failed — {exc}]")
        raise
    store.save_message(contact_id, "ai", output)
    return output
