from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        # Documentation: https://pypi.org/project/aidial-client/
        # Create synchronous and asynchronous Dial clients using shared API key.
        self._client = Dial(
            api_key=self._api_key,
            base_url=DIAL_ENDPOINT,
        )
        self._async_client = AsyncDial(
            api_key=self._api_key,
            base_url=DIAL_ENDPOINT,
        )

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create chat completion with sync client
        completion = self._client.chat.completions.create(
            deployment_name=self._deployment_name,
            stream=False,
            messages=[msg.to_dict() for msg in messages],
            api_version="2024-02-15-preview",
        )

        # 2. Extract content and return assistant message
        if not completion.choices:
            raise Exception("No choices in response found")

        content = completion.choices[0].message.content or ""
        print(f"AI: {content}")
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create chat completion with async client in streaming mode
        completion = await self._async_client.chat.completions.create(
            deployment_name=self._deployment_name,
            stream=True,
            messages=[msg.to_dict() for msg in messages],
            api_version="2024-02-15-preview",
        )

        # 2. Collect content chunks
        contents: list[str] = []

        # 3. Iterate over streaming chunks
        async for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content_piece = getattr(delta, "content", None)
            if content_piece:
                print(content_piece, end="", flush=True)
                contents.append(content_piece)

        # 5. Print empty row to move input to a new line
        print()

        # 6. Return full assistant message
        full_content = "".join(contents)
        return Message(role=Role.AI, content=full_content)
