# consumers.py

import json
import logging
from concurrent.futures import ThreadPoolExecutor

from channels.db import database_sync_to_async  # type: ignore
from channels.exceptions import StopConsumer  # type: ignore
from channels.generic.websocket import AsyncJsonWebsocketConsumer  # type: ignore
from django.contrib.auth.models import AnonymousUser

from components.chat_data_processor import ChatDataProcessor
from components.config import config
from components.docker_interface import DockerManager
from components.lang_model_service import LLMClient
from .models import Conversation

logger = logging.getLogger(__name__)


class GenerateConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.docker_manager = DockerManager()
        self.llm_client = LLMClient()
        self.chat_data_processor: ChatDataProcessor | None = None
        self.conversation: Conversation | None = None

    async def connect(self) -> None:
        await self.accept()
        config.reload()
        executor = ThreadPoolExecutor()
        executor.submit(self.docker_manager.start_container)

        self.chat_data_processor = ChatDataProcessor(self.docker_manager, self, self.llm_client)

    async def disconnect(self, close_code: int) -> None:
        executor = ThreadPoolExecutor()
        executor.submit(self.docker_manager.remove_container)
        raise StopConsumer()

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None, **kwargs) -> None:
        if text_data is None:
            return
        data = json.loads(text_data)
        prompt_text = data.get("prompt", "")
        model_name = data.get("model", "")
        test_input = data.get("test_input", "")

        if self.conversation is None:
            # noinspection PyUnresolvedReferences
            self.conversation = await self.create_conversation(model_name)
        # else:
        #     await self.conversation.save()
        #     Message.objects.create(conversation=self.conversation, text=prompt_text, is_system=False)

        if not self.chat_data_processor:
            raise Exception("Chat data processor not initialized.")
        await self.chat_data_processor.process_prompt(prompt_text, model_name=model_name, test_input=test_input)

    async def send(self, text_data: str | None = None, bytes_data: bytes | None = None, close: bool = False) -> None:
        pass

    @database_sync_to_async
    def create_conversation(self, model_name: str) -> Conversation:
        user = self.scope["user"]
        if isinstance(user, AnonymousUser):
            user = None
        elif hasattr(user, "_wrapped"):
            # noinspection PyProtectedMember
            user = user._wrapped
        return Conversation.objects.create(gpt_model_name=model_name, user=user)
