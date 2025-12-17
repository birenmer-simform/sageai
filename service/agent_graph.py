"""
LangGraph-based chat agent that injects long-term and short-term memory into the prompt.

This keeps our existing Mongo-backed memory/chat history but replaces the basic
one-shot chat call with a tiny agent graph:
    START -> load_context (fetch LTM/STM, build system message) -> call_model -> END
"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START

from prompts.system_prompt import SystemPrompt
from service.db import MongoStorage


class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], "Conversation history including latest user turn"]


def _build_memory_system_prompt(
    base_prompt: str,
    ltm: Optional[dict],
    stm: Optional[dict],
) -> str:
    """
    Build a system prompt that incorporates long-term and short-term memory snapshots.
    """
    lines = [base_prompt.strip()]

    if ltm:
        lines.append("\n[Long-term memory]")
        profile = ltm.get("profile") or {}
        prefs = ltm.get("preferences") or {}
        background = ltm.get("background")
        topics = ltm.get("topics") or []
        if profile:
            lines.append(f"- Profile: {profile}")
        if prefs:
            lines.append(f"- Preferences: {prefs}")
        if background:
            lines.append(f"- Background: {background}")
        if topics:
            lines.append(f"- Topics: {topics}")

    if stm:
        lines.append("\n[Short-term memory]")
        task = stm.get("task")
        topic = stm.get("topic")
        temp_prefs = stm.get("temporary_preferences") or {}
        if task:
            lines.append(f"- Task: {task}")
        if topic:
            lines.append(f"- Topic: {topic}")
        if temp_prefs:
            lines.append(f"- Temporary preferences: {temp_prefs}")

    return "\n".join(lines)


def build_chat_agent(
    storage: MongoStorage,
    llm: ChatOpenAI,
    user_id: str,
    chat_id: str,
    base_system_prompt: Optional[str] = None,
):
    """
    Create a compiled LangGraph chat agent bound to the given user/chat.
    """
    system_prompt_text = base_system_prompt or SystemPrompt().get_prompt()

    async def load_context(state: ChatState) -> ChatState:
        ltm = await storage.read_long_term(user_id)
        stm = await storage.read_short_term(chat_id, user_id)

        system_text = _build_memory_system_prompt(system_prompt_text, ltm, stm)
        system_message = SystemMessage(content=system_text)

        # Ensure the system message is the first message in the sequence.
        new_messages: List[BaseMessage] = [system_message]
        new_messages.extend(state["messages"])
        return {"messages": new_messages}

    def call_model(state: ChatState) -> ChatState:
        response = llm.invoke(state["messages"])
        ai_msg = AIMessage(content=response.content)
        return {"messages": [*state["messages"], ai_msg]}

    graph = StateGraph(ChatState)
    graph.add_node("load_context", load_context)
    graph.add_node("call_model", call_model)
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "call_model")
    graph.add_edge("call_model", END)

    return graph.compile()


def build_message_history(history: List[dict]) -> List[BaseMessage]:
    """
    Convert stored history rows into LangChain message objects.
    Expects items shaped like {"role": "user"|"assistant"|"system", "content": "..."}.
    """
    messages: List[BaseMessage] = []
    for item in history or []:
        role = item.get("role")
        content = item.get("content", "")
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    return messages


__all__ = ["ChatState", "build_chat_agent", "build_message_history"]
