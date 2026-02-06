import asyncio

from task.clients.client import DialClient
from task.clients.custom_client import CustomDialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    """
    Start interactive chat session with DIAL API.
    """
    # 1.1/1.2 Ask for deployment name and which client to use
    deployment_name = input(
        "Enter deployment name (e.g. 'gpt-4o') or press 'enter' for default 'gpt-4o':\n> "
    ).strip() or "gpt-4o"

    use_custom = (
        input("Use CustomDialClient (raw HTTP) instead of SDK client? (y/N):\n> ")
        .strip()
        .lower()
        == "y"
    )

    sdk_client = DialClient(deployment_name)
    custom_client = CustomDialClient(deployment_name)
    client = custom_client if use_custom else sdk_client

    # 2. Create Conversation object
    conversation = Conversation()

    # 3. Get System prompt from console or use default
    print("Provide System prompt or press 'enter' to continue.")
    system_prompt = input("> ").strip() or DEFAULT_SYSTEM_PROMPT
    conversation.add_message(Message(role=Role.SYSTEM, content=system_prompt))

    # 4. Interactive loop
    print("\nType your question or 'exit' to quit.")
    while True:
        user_input = input("> ").strip()

        # 5. Exit condition
        if user_input.lower() == "exit":
            print("Exiting the chat. Goodbye!")
            break

        if not user_input:
            continue

        # 6. Add user message to history
        user_message = Message(role=Role.USER, content=user_input)
        conversation.add_message(user_message)

        # 7. Call appropriate completion method
        messages = conversation.get_messages()

        if stream:
            print("AI: ", end="", flush=True)
            ai_message = await client.stream_completion(messages)
        else:
            ai_message = client.get_completion(messages)

        # 8. Add generated message to history
        conversation.add_message(ai_message)


if __name__ == "__main__":
    asyncio.run(start(True))
