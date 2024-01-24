import logging
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class LLMApi:
    url: str
    key: str
    max_context_tokens: int
    max_output_tokens: int = 0


def get_project_name() -> str:
    config_file = Path(__file__).parent.parent / "pyproject.toml"
    toml_content = load_toml_file(config_file)
    if (
        "tool" not in toml_content
        or "poetry" not in toml_content["tool"]
        or "name" not in toml_content["tool"]["poetry"]
    ):
        raise KeyError("The required [tool.poetry.name] field is missing in pyproject.toml.")

    project_name = toml_content["tool"]["poetry"]["name"]
    return project_name


def load_toml_file(file_path: Path) -> dict:
    try:
        with open(file_path, "rb") as file:
            return tomllib.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"TOML file not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied when accessing the TOML file: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error parsing TOML file {file_path}: {e}")


class Config:
    home_dir = Path.home()
    dotenv_path = home_dir / ".config" / get_project_name() / ".env"
    load_dotenv(dotenv_path)

    def __init__(self) -> None:
        self._toml_config: dict[str, dict[str, str]] = {}
        self.SYSTEM_MESSAGES_FILE = Path(__file__).parent.parent / "data" / "system_messages.toml"
        self.SYSTEM_MESSAGES: dict[str, str] = {}
        self.TEST_INPUT = ""
        self._load_system_messages()

    def _load_system_messages(self) -> None:
        self._toml_config = load_toml_file(self.SYSTEM_MESSAGES_FILE)
        languages = ["python"]
        if not languages:
            logger.warning("No languages found in system_messages.toml.")
        for language in languages:
            system_message = self._toml_config["SYSTEM_MESSAGE"].get(language, "")
            self.SYSTEM_MESSAGES[language] = system_message
        self.TEST_INPUT = self._toml_config["TEST_MESSAGES"].get("input", "")

    def reload(self) -> None:
        self._load_system_messages()

    MINIMUM_COMPLETION_TOKENS = 100

    _DOCKER_HOST = "docker.local"
    _DOCKER_PORT = 2375

    DOCKER_URL = f"tcp://{_DOCKER_HOST}:{_DOCKER_PORT}"
    DOCKET_DETACH_TIMEOUT = 10

    _POSTGRES_HOST = "localhost"
    _POSTGRES_DATABASE = "fastgpt"

    PSQL_URL = f"postgresql+asyncpg://{_POSTGRES_HOST}/{_POSTGRES_DATABASE}"

    REDIS_HOST = "docker.local"
    REDIS_PORT = 6379

    SLEEP_DURATION = 0.00001
    LLM_LOADING_TIMEOUT = 60

    RECOGNIZED_LANGUAGES = ["python", "js", "javascript", "bash"]

    PYLINT_DISABLED_CHECKS = ["C0114", "C0116"]

    # noinspection SpellCheckingInspection
    LLM_APIS: dict[str, LLMApi] = {
        "deepseek-coder-33b": LLMApi(
            url="http://localhost:8080/v1",
            key="sk-2f2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b",
            max_context_tokens=4 * 1024,
        ),
        "phind-codellama-34": LLMApi(
            url="http://localhost:8080/v1",
            key="sk-2f2b2b2b2b2b2b2b2b2b2b2b2b2b2b",
            max_context_tokens=4 * 1024,
        ),
        "gpt-4": LLMApi(
            url="https://api.openai.com/v1",
            key=os.environ["OPENAI_API_KEY"],
            max_context_tokens=8 * 1024,
        ),
        "gpt-4-1106-preview": LLMApi(
            url="https://api.openai.com/v1",
            key=os.environ["OPENAI_API_KEY"],
            max_context_tokens=120_000,
            max_output_tokens=4 * 1024,
        ),
        "gpt-3.5-turbo-16k": LLMApi(
            url="https://api.openai.com/v1",
            key=os.environ["OPENAI_API_KEY"],
            max_context_tokens=16 * 1024,
        ),
        "gpt-3.5-turbo-1106": LLMApi(
            url="https://api.openai.com/v1",
            key=os.environ["OPENAI_API_KEY"],
            max_context_tokens=16 * 1024,
            max_output_tokens=4 * 1024,
        ),
    }


config = Config()
