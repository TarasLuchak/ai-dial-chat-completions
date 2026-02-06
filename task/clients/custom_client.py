import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    _endpoint: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = (
            DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"
        )

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers with API key and content type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        # 2. Prepare request body
        request_data = {
            "messages": [msg.to_dict() for msg in messages],
        }

        # Print full request for debugging
        print("=== CustomDialClient request ===")
        print(json.dumps(request_data, indent=2))

        # 3. Send POST request
        response = requests.post(self._endpoint, headers=headers, json=request_data)

        # 5. Handle non-success status codes
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        # Print raw response for debugging
        print("=== CustomDialClient response ===")
        print(response.text)

        # 4. Extract content from JSON response
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise Exception("No choices in response found")

        content = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )
        print(f"AI: {content}")
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers with API key and content type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        # 2. Prepare request body for streaming
        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages],
        }

        contents: list[str] = []

        print("=== CustomDialClient streaming request ===")
        print(json.dumps(request_data, indent=2))

        # 4. Create aiohttp session and send request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._endpoint,
                headers=headers,
                json=request_data,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {body}")

                # 6. Read streamed chunks line by line
                async for raw_chunk in resp.content:
                    text = raw_chunk.decode("utf-8")
                    for line in text.splitlines():
                        snippet = self._get_content_snippet(line)
                        if snippet:
                            print(snippet, end="", flush=True)
                            contents.append(snippet)

        print()
        full_content = "".join(contents)
        return Message(role=Role.AI, content=full_content)

    def _get_content_snippet(self, chunk_line: str) -> str:
        """
        Parse a single streaming line that starts with 'data: ' and
        return the content snippet, or an empty string if none.
        """
        if not chunk_line.startswith("data: "):
            return ""

        payload = chunk_line[len("data: ") :].strip()
        if payload == "[DONE]":
            return ""

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return ""

        choices = data.get("choices") or []
        if not choices:
            return ""

        delta = choices[0].get("delta") or {}
        return delta.get("content", "") or ""

