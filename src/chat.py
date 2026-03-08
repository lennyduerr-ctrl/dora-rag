"""Simple CLI chat for testing the DORA RAG agent.

Usage:
    python -m src.chat
"""

import uuid
from src.chain import create_dora_agent


def main():
    print("=" * 60)
    print("DORA Compliance Chatbot (CLI)")
    print("Stelle Fragen zur DORA-Verordnung. 'quit' zum Beenden.")
    print("=" * 60)

    agent = create_dora_agent()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}

    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not question or question.lower() in ("quit", "exit", "q"):
            break

        print()
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config=config,
        )
        print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
