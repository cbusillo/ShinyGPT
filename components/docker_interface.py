# docker_interaction.py
import base64
import logging
import threading
from datetime import datetime
from time import sleep
from typing import Generator

import docker
from docker.models.containers import Container

from components.config import config

logger = logging.getLogger(__name__)


class DockerManager:
    def __init__(self, image: str = "python:3.11") -> None:
        self.client = docker.DockerClient(base_url=config.DOCKER_URL)
        self.image = image
        self.container: Container | None = None

    def start_container(self) -> None:
        logger.info("Starting docker container.")
        self.container = self.client.containers.run(image=self.image, detach=True, tty=True, stdin_open=True)
        self._create_app_directory()

    def remove_container(self) -> None:
        self._wait_for_container()
        if not self.container:
            return

        self.container.stop()
        self.container.remove(force=True)
        self.container = None

    def _create_app_directory(self) -> None:
        if not self.container:
            return
        self.container.exec_run(cmd="mkdir -p /app")

    def execute_bash_generator(self, command: str) -> Generator[str, None, None]:
        exec_instance = self.execute_bash_return_exec_instance(command)

        return exec_instance.get_output()

    def execute_bash_string(self, command: str) -> tuple[int, str]:
        exec_instance = self.execute_bash_return_exec_instance(command)

        return exec_instance.get_exit_code() or 0, exec_instance.get_output_string()

    def execute_bash_return_exec_instance(self, command: str) -> "ExecInstance":
        self._wait_for_container()

        logger.debug(f"Executing bash command: {command}")

        encoded_command = base64.b64encode(command.encode()).decode()
        command_str = f"echo {encoded_command} | base64 --decode | /bin/bash"

        exec_instance = ExecInstance(self.container, command_str)
        exec_instance.start()

        monitor_thread = threading.Thread(target=exec_instance.monitor, args=(config.DOCKET_DETACH_TIMEOUT,))
        monitor_thread.start()
        return exec_instance

    def save_python_script(self, code: str) -> str:
        filename = f"script_{datetime.now().strftime('%Y%m%d%H%M%S')}.py"
        filepath = f"/app/{filename}"

        command = f"cat <<EOF > {filepath}\n{code}\nEOF"
        self.execute_bash_string(command)

        return filepath

    def execute_python_string(self, code: str) -> tuple[int, str]:
        python_script_path = self.save_python_script(code)
        error_code, output = self.execute_python_script(python_script_path)
        return error_code, output

    def execute_python_script(self, file_path: str) -> tuple[int, str]:
        error_code, output = self.execute_bash_string(f"python {file_path}")
        return error_code, output

    def execute_pip_install(self, packages: set[str]) -> str:
        outputs = []
        for package in packages:
            install_command = f"pip install {package} -v"
            exit_code, _output = self.execute_bash_string(install_command)

            if exit_code != 0:
                outputs.append(f"Failed to install package {package}")
            else:
                outputs.append(f"Successfully installed package {package}")

        return "\n".join(outputs)

    def _wait_for_container(self) -> None:
        retries = 20
        while retries > 0:
            if self.container:
                return
            retries -= 1
            sleep(1)
        logger.warning("Failed to start container.")


class ExecInstance:
    def __init__(self, container, command) -> None:
        self.container = container
        self.command = command
        self.exec_id = None
        self.output_generator = None

    def start(self) -> None:
        exec_instance = self.container.client.api.exec_create(
            self.container.id, cmd=["/bin/bash", "-c", self.command], workdir="/app"
        )
        self.exec_id = exec_instance["Id"]
        self.output_generator = self.container.client.api.exec_start(self.exec_id, stream=True, detach=True)

    def monitor(self, timeout) -> None:
        start_time = datetime.now()
        while True:
            sleep(1)
            exec_inspect = self.container.client.api.exec_inspect(self.exec_id)
            if exec_inspect["Running"]:
                if (datetime.now() - start_time).seconds > timeout:
                    self.container.client.api.close(self.exec_id)
                    return
            else:
                break

    def get_output(self) -> Generator[str, None, None]:
        if not self.output_generator:
            return
        for line in self.output_generator:
            yield line.decode("utf-8")

    def get_exit_code(self) -> int:
        exec_inspect = self.container.client.api.exec_inspect(self.exec_id)
        return exec_inspect["ExitCode"]

    def get_output_string(self) -> str:
        output_lines = list(self.get_output())
        return "".join(output_lines)
