import os
import re
import subprocess
import inspect
import asyncio
import time
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
        # Read logs from the build process
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

        # Read logs with a timer; break out after 3 seconds
        start_time = time.time()
        while True:
            line = up_process.stdout.readline()
            if not line:
                break
            print(line, end="")
            full_output += line

            # Capture error output based on traceback patterns
            if re.match(r'\s*File\s+".+",\s+line\s+\d+', line):
                traceback_started = True
                error_capture.append(line)
            elif traceback_started:
                error_capture.append(line)
            elif "Traceback" in line or "SyntaxError" in line or "Exception" in line:
                traceback_started = True
                error_capture.append(line)

            # Check if the container exited with an error message
            if "exited with code" in line:
                error_output = "".join(error_capture)
                break

            # Check if 3 seconds have elapsed; if so, break out of the loop
            if time.time() - start_time > 3:
                print("3 seconds passed, stopping log capture...")
                break

        # Kill the container process if it's still running
        # Reads the container logs, and if the container does not stop on its own (e.g., a live service), log reading is interrupted after 3 seconds.
        try:
            up_process.kill()
        except Exception:
            pass

        # If errors were captured or the container exited with a failure code,
        # fetch more detailed logs from the container.
        if (
            up_process.returncode is not None and up_process.returncode != 0
        ) or error_output:
            print(f"Fetching logs from the container: {container_name}...")
            log_process = await asyncio.create_subprocess_exec(
                "docker",
                "logs",
                container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            log_stdout, log_stderr = await log_process.communicate()
            log_output = (
                log_stdout.decode().strip()
                if isinstance(log_stdout, bytes)
                else log_stdout
            )

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
        # Clean up: bring down containers and prune images if no error occurred
        if error is None:
            subprocess.run(["docker-compose", "down"])
            subprocess.run(["docker", "image", "prune", "-f"])
        os.chdir(original_dir)  # Restore working directory

    return {"error": None}
