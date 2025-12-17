"""Basic OpenAI chat service using langchain-openai (gpt-4.1)."""

from typing import List, Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from prompts.system_prompt import SystemPrompt

Role = Literal["system", "user", "assistant"]


class ChatService:
    def __init__(
        self,
        model: str = "gpt-4.1",
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> None:
        self.model = model
        # self.system_prompt = system_prompt or "You are a helpful assistant."
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
        )

    def build_messages(
        self,
        user_message: str,
        history: Optional[List[dict]] = None,
    ) -> List[SystemMessage | HumanMessage | AIMessage]:
        """
        Construct the messages array for the chat completion.

        History may be provided as a list of {"role": ..., "content": ...} where
        role ∈ {"user", "assistant", "system"}.
        """
        messages: List[SystemMessage | HumanMessage | AIMessage] = [
            SystemMessage(content=SystemPrompt().get_prompt())
        ]
        if history:
            for item in history:
                role = item.get("role")
                content = item.get("content", "")
                if role == "assistant":
                    messages.append(AIMessage(content=content))
                elif role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "system":
                    messages.append(SystemMessage(content=content))
        messages.append(HumanMessage(content=user_message))
        return messages

    def chat(
        self,
        user_message: str,
        history: Optional[List[dict]] = None,
    ) -> str:
        """Send a prompt via langchain-openai and return the assistant reply text."""
        messages = self.build_messages(user_message, history)
        result = self.llm.invoke(messages)
        return result.content or ""


__all__ = ["ChatService", "Role"]
