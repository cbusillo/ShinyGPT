# data_processor.py
import logging
from asyncio import sleep
from pathlib import Path

from channels.generic.websocket import AsyncJsonWebsocketConsumer  # type: ignore

from components.code_validation import CodeValidator
from components.config import config
from components.docker_interface import DockerManager
from components.lang_model_service import LLMClient

logger = logging.getLogger(__name__)


class ChatDataProcessor:
    def __init__(
        self, docker_manager: DockerManager, consumer: AsyncJsonWebsocketConsumer, llm_client: LLMClient
    ) -> None:
        self.docker_manager = docker_manager
        self.consumer = consumer
        self.llm_client = llm_client

    async def process_prompt(self, prompt_text: str, model_name: str, test_input: bool) -> None:
        if test_input:
            full_response = config.TEST_INPUT
            await self.consumer.send_json({"response": full_response})
            await sleep(config.SLEEP_DURATION)
        else:
            response_generator = self.llm_client.send_prompt(prompt_text, model_name)
            full_response = ""
            async for chunk in response_generator:
                if not chunk:
                    continue
                full_response += chunk
                await self.consumer.send_json({"response": chunk})
                await sleep(config.SLEEP_DURATION)
        if full_response:
            self.write_response_to_file(full_response)
            await self.process_code_blocks(full_response)

    @staticmethod
    def write_response_to_file(response: str) -> None:
        data_folder = Path(__file__).resolve().parent.parent / "data"
        data_folder.mkdir(exist_ok=True)
        file_path = data_folder / "test_input.log"
        with file_path.open("w") as file:
            file.write(response)

    async def process_code_blocks(self, full_response: str) -> None:
        code_blocks_with_language = CodeValidator.extract_code_blocks(full_response)
        if not code_blocks_with_language:
            return
        for language, code_block in code_blocks_with_language:
            await self.process_code_block(code_block, language)

    async def process_code_block(self, code_block: str, language) -> None:
        if language in ["bash", "sh", "shell"]:
            bash_output = self.docker_manager.execute_bash_generator(code_block)

            await self.consumer.send_json({"code": f"Executing:\n{code_block}\nResult:"})
            for line in bash_output:
                await self.consumer.send_json({"code": line})
                await sleep(config.SLEEP_DURATION)
            await self.consumer.send_json({"code": "=" * 50})
            await sleep(config.SLEEP_DURATION)

        if language in ["py", "python"] and CodeValidator.is_valid_python(code_block):
            formatted_code = CodeValidator.format_with_black(code_block)
            code_imports = CodeValidator.extract_python_imports(formatted_code)
            pip_output = self.docker_manager.execute_pip_install(code_imports)

            await self.consumer.send_json({"code": pip_output})
            await sleep(config.SLEEP_DURATION)
            (
                error_count,
                warning_count,
                messages,
            ) = CodeValidator.run_pylint_static_analysis(formatted_code)
            if error_count > 0:
                logger.error(f"Code block has {error_count} errors, {warning_count} warnings: {messages}")

            await self.execute_and_send_code(formatted_code)

    async def execute_and_send_code(self, code: str) -> None:
        docker_output = self.docker_manager.execute_python_string(code)
        await self.consumer.send_json({"code": docker_output})
        await sleep(config.SLEEP_DURATION)
