import argparse
import asyncio
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

from service.chat_service import ChatService
from service.db import MongoStorage
from schemas import ChatCreate, ConversationCreate
from prompts import SystemPrompt

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Basic LangChain OpenAI chat loop with Mongo persistence."
    )
    parser.add_argument("--model", default="gpt-4.1", help="OpenAI chat model to use.")
    # parser.add_argument("--system", default="You are a helpful assistant.", help="System prompt to prepend.")
    parser.add_argument("--temperature", type=float, default=0.3, help="Sampling temperature.")
    parser.add_argument("--max-tokens", type=int, default=500, help="Max tokens per response.")
    parser.add_argument("--user-id", default="demo-user", help="User ID for chat and memory records.")
    parser.add_argument("--chat-id", default=None, help="Existing chat/thread ID to resume (ObjectId string).")
    parser.add_argument("--title", default=None, help="Optional title when creating a new chat.")
    return parser.parse_args()


async def run_chat() -> None:
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your environment before running.")
        return

    mongo_uri = os.getenv("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB")
    if not mongo_uri or not mongo_db:
        print("Please set MONGO_URI and MONGO_DB in your environment (see .env).")
        return

    args = parse_args()

    storage = MongoStorage(mongo_uri, mongo_db)
    await storage.ensure_indexes()

    chat_id: Optional[str] = args.chat_id
    if not chat_id:
        chat_doc = await storage.create_chat(
            ChatCreate(user_id=args.user_id, title=args.title, status="active")
        )
        chat_id = chat_doc.id
        print(f"Created new chat thread: {chat_id}")
        # Persist the system prompt as the initial system message for this chat
        await storage.insert_message(
            ConversationCreate(
                chat_id=chat_id,
                user_id=args.user_id,
                sender="system",
                content=SystemPrompt().get_prompt(),
            )
        )
    else:
        print(f"Resuming chat thread: {chat_id}")

    # Load recent history for context
    history: List[Dict[str, str]] = await storage.get_recent_history(chat_id, limit=20)

    chat = ChatService(
        model=args.model,
        system_prompt=args.system,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    print("Starting chat. Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("you: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Bye.")
            break

        # Persist user message
        await storage.insert_message(
            ConversationCreate(
                chat_id=chat_id,
                user_id=args.user_id,
                sender="user",
                content=user_input,
            )
        )

        # Generate assistant reply (run in thread to avoid blocking loop)
        reply = await asyncio.to_thread(chat.chat, user_input, history=history)

        print(f"assistant: {reply}")

        # Persist assistant message
        await storage.insert_message(
            ConversationCreate(
                chat_id=chat_id,
                user_id=args.user_id,
                sender="assistant",
                content=reply,
            )
        )

        # Track conversation history for context
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": reply})


def main() -> None:
    asyncio.run(run_chat())


if __name__ == "__main__":
    main()
