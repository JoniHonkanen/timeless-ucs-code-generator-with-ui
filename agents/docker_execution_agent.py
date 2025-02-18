import os
import re
import subprocess
import inspect
import asyncio
from schemas import GraphState, ErrorMessage


async def start_docker_container_agent(state: GraphState):
    print("*** START DOCKER CONTAINER AGENT ***")
    error = None
    current_function = inspect.currentframe().f_code.co_name
    current_file = __file__

    container_name = state["docker_container_name"]
    original_dir = os.getcwd()
    os.chdir("generated/src")

    full_output = ""
    error_output = ""
    error_capture = []
    traceback_started = False

    try:
        # Build image
        print(f"Building Docker image for container: {container_name}...")
        build_command = ["docker-compose", "build"]
        build_process = subprocess.Popen(
            build_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )
        # get logs from the build process
        for line in build_process.stdout:
            print(line, end="")
            full_output += line

        build_process.wait()
        if build_process.returncode != 0:
            error = ErrorMessage(
                type="Docker Configuration Error",
                message="Error during Docker setup or build process.",
                details=full_output.strip(),
                code_reference=f"{current_file} - {current_function}",
            )
            return {"error": error}

        # Run container
        print(f"Running Docker container: {container_name}...")
        up_command = [
            "docker-compose",
            "up",
            "--abort-on-container-exit",
            "--no-log-prefix",  # Cleaner log output
        ]
        up_process = subprocess.Popen(
            up_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        # get logs from the process
        for line in up_process.stdout:
            print(line, end="")
            full_output += line

            # Capture error output
            if re.match(r'\s*File\s+".+",\s+line\s+\d+', line):
                traceback_started = True
                error_capture.append(line)
            elif traceback_started:
                error_capture.append(line)
            elif "Traceback" in line or "SyntaxError" in line or "Exception" in line:
                traceback_started = True
                error_capture.append(line)

            # Check if the container exited with an error
            if "exited with code" in line:
                error_output = "".join(error_capture)
                break

        # Ensure long-running services don't block execution (live server etc.)
        # so we can proceed the agent workflow
        try:
            up_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print(
                f"Container {container_name} is still running after 3 seconds, proceeding to cleanup..."
            )

        # Handle errors if container exits with failure
        if up_process.returncode != 0 or error_output:
            print(f"Fetching logs from the container: {container_name}...")
            log_process = await asyncio.create_subprocess_exec(
                "docker",
                "logs",
                container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            log_stdout, log_stderr = await log_process.communicate()
            log_output = log_stdout.decode().strip()

            error = ErrorMessage(
                type="Docker Execution Error",
                message="The code inside the container encountered an error or failed execution.",
                details=error_output or log_output,
                code_reference=f"{current_file} - {current_function}",
            )

            return {"error": error}

        state["docker_output"] = full_output

    except Exception as e:
        # Catch any unexpected errors
        error = ErrorMessage(
            type="Unexpected Docker Error",
            message="An unexpected error occurred while communicating with Docker.",
            details=str(e),
            code_reference=f"{current_file} - {current_function}",
        )
        return {"error": error}

    finally:
        # Clean up, so stop containers etc.
        if error is None:
            subprocess.run(["docker-compose", "down"])
            subprocess.run(["docker", "image", "prune", "-f"])

        os.chdir(original_dir) # Restore working directory

    return {"error": None}
