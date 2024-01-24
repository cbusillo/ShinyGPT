# llm_communication.py
import json
import logging
import subprocess
import time
from asyncio import sleep
from glob import glob
from pathlib import Path
from typing import AsyncGenerator, Generator
from urllib.parse import urlparse

import requests
import openai
from openai import AsyncStream
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from transformers import GPT2Tokenizer  # type: ignore

from components.config import config

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        self.models = {}
        for llm_model_name, llm_api in config.LLM_APIS.items():
            llm_api_url = llm_api.url
            llm_api_key = llm_api.key
            self.models[llm_model_name] = openai.AsyncOpenAI(
                base_url=llm_api_url,
                api_key=llm_api_key,
            )
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

    async def send_prompt(self, prompt_text: str, model_name: str) -> AsyncGenerator[str, None]:
        llm_api = config.LLM_APIS[model_name]

        if "local" in llm_api.url:
            await self.check_and_start_local_server(model_name)

        system_message = ChatCompletionSystemMessageParam(role="system", content=self._get_system_message())
        user_message = ChatCompletionUserMessageParam(role="user", content=prompt_text)

        api_message = [system_message, user_message]
        if llm_api.max_output_tokens:
            adjusted_max_tokens = llm_api.max_output_tokens
        else:
            num_tokens_used = sum(
                len(
                    self.tokenizer.encode(
                        message.get("content", ""),
                        add_special_tokens=True,
                        max_length=llm_api.max_context_tokens,
                        truncation=True,
                    )
                )
                for message in [system_message, user_message]
            )
            adjusted_max_tokens = llm_api.max_context_tokens - num_tokens_used

        min_tokens = int(config.MINIMUM_COMPLETION_TOKENS)
        if adjusted_max_tokens <= min_tokens:
            message = f"Adjusted max tokens ({adjusted_max_tokens}) is too low for model {model_name}"
            logger.warning(message)
            yield message
            return
        try:
            current_model = self.models[model_name]
            response = await current_model.chat.completions.create(
                model=model_name,
                messages=api_message,
                max_tokens=adjusted_max_tokens,
                stream=True,
            )
            if not isinstance(response, AsyncStream):
                raise TypeError(f"Expected AsyncStream, got {type(response)}")
            async for chunk in response:
                content = chunk.choices[0].delta.content
                yield content or ""
                if not content:
                    logger.warning(f"OpenAI API returned empty response: {chunk}")

        except Exception as e:
            if isinstance(e, openai.Timeout):
                logger.warning(f"OpenAI API request timed out: {e}")
            elif isinstance(e, openai.BadRequestError):
                logger.warning(f"OpenAI API request failed to connect: {e}")
            elif isinstance(e, openai.BadRequestError):
                logger.warning(f"OpenAI API request was invalid: {e}")
            elif isinstance(e, openai.APIError):
                logger.warning(f"OpenAI API returned an API Error: {e}")
            elif isinstance(e, openai.AuthenticationError):
                logger.warning(f"OpenAI API request was not authorized: {e}")
            elif isinstance(e, openai.PermissionDeniedError):
                logger.warning(f"OpenAI API request was not permitted: {e}")
            elif isinstance(e, openai.RateLimitError):
                logger.warning(f"OpenAI API request exceeded rate limit: {e}")
            else:
                raise

    @staticmethod
    def _get_system_message(language: str = "python") -> str:
        system_message = config.SYSTEM_MESSAGES[language]
        return system_message

    async def check_and_start_local_server(self, model_name: str) -> None:
        model_url = config.LLM_APIS[model_name].url

        try:
            requests.get(f"{model_url}/health")
        except requests.exceptions.ConnectionError:
            process = self.start_local_server(model_name)
            await self.wait_for_model_to_load(process)

    @staticmethod
    def start_local_server(model_name: str) -> subprocess.Popen:
        model_url = str(config.LLM_APIS[model_name].url)
        model_port = urlparse(model_url).port
        model_port_str = str(model_port)

        script_path = Path(__file__).parent
        project_root = script_path.parent.absolute()
        server_binary = project_root / "external" / "llama.cpp" / "server"
        model_pattern = str(project_root / "data" / "llm_files" / (model_name + "*" + "Q4" + "*.gguf"))

        if len(model_pattern) == 0:
            raise FileNotFoundError(f"Model file not found for {model_name}")
        model_file = glob(model_pattern)[0]
        command = [str(server_binary), "--port", model_port_str, "-m", model_file]
        logger.info(f"Starting local server using '{' '.join(command)}'")
        return subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True, start_new_session=True)

    @staticmethod
    async def wait_for_model_to_load(process: subprocess.Popen) -> None:
        start_time = time.time()
        while True:
            if not process.stdout:
                await sleep(0.1)
                continue
            output = process.stdout.readline().strip()
            if output:
                logger.info(output)
                try:
                    log = json.loads(output)
                    if log.get("message") == "model loaded":
                        break
                except json.JSONDecodeError:
                    pass
            if time.time() - start_time > config.LLM_LOADING_TIMEOUT:
                raise RuntimeError(f"Timeout waiting for model to load")
            await sleep(0.001)

        if process.poll() is not None and process.returncode != 0:
            raise RuntimeError(f"Process exited with code {process.returncode}")

    @staticmethod
    def get_model_names() -> Generator[str, None, None]:
        for model_name in config.LLM_APIS.keys():
            yield model_name
