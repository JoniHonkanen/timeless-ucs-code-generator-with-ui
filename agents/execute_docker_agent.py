import os
import asyncio
import inspect
from schemas import GraphState, ErrorMessage


async def execute_docker_agent(state: GraphState):
    print("\n **EXECUTE DOCKER AGENT **")
    error = None
    current_function = inspect.currentframe().f_code.co_name
    current_file = __file__
    container_name = state["docker_container_name"]

    try:
        print(f"Building and starting Docker container: {container_name}...")
        compose_file_path = os.path.join("generated/src", "compose.yaml")
        compose_command = ["docker-compose", "-f", compose_file_path, "up", "--build"]

        setup_process = await asyncio.create_subprocess_exec(
            *compose_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        setup_stdout, setup_stderr = await setup_process.communicate()

        if setup_process.returncode != 0:
            error = ErrorMessage(
                type="Docker Configuration Error",
                message="Error during Docker setup or build process.",
                details=setup_stderr.decode().strip(),
                code_reference=f"{current_file} - {current_function}",
            )
            print(f"Error during Docker setup: {setup_stderr.decode()}")
            return {"error": error}

        print("Docker setup and build completed successfully.")
        print("Docker Setup Output:\n", setup_stdout.decode())

        print(f"Fetching logs from the container: {container_name}...")
        log_process = await asyncio.create_subprocess_exec(
            "docker",
            "logs",
            container_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        log_stdout, log_stderr = await log_process.communicate()
        logs = log_stdout.decode()

        if "Traceback" in logs or "Error" in logs or log_stderr.decode().strip():
            error = ErrorMessage(
                type="Docker Execution Error",
                message="The code inside the container encountered an error.",
                details=log_stderr.decode().strip(),
                code_reference=f"{current_file} - {current_function}",
            )
            print(f"Error during container execution: {log_stderr.decode()}")
        else:
            print("Container Logs:\n", logs)

    except Exception as e:
        error = ErrorMessage(
            type="Unexpected Docker Error",
            message="An unexpected error occurred while communicating with Docker.",
            details=str(e),
            code_reference=f"{current_file} - {current_function}",
        )
        print(error.json())

    if error:
        print(error.json())

    return {"error": error}
