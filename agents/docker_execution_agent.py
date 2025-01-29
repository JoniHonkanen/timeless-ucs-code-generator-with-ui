import os
import re
import subprocess
from schemas import GraphState, ErrorMessage

async def execute_docker_agent(state: GraphState, file_path: str):
    print("\n **EXECUTE DOCKER AGENT **")
    logs_buffer = []
    error_output = ""  # Captures the traceback lines

    try:
        os.chdir(file_path)
        print("Building Docker image...")
        build_command = ["docker-compose", "build"]
        build_process = subprocess.Popen(
            build_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        # Capture build logs
        for line in build_process.stdout:
            print(line, end="")
            logs_buffer.append(line)

        build_process.wait()
        if build_process.returncode != 0:
            raise Exception("Docker image build failed")

        print("Running Docker container...")
        up_command = [
            "docker-compose",
            "up",
            "--abort-on-container-exit",
            "--no-log-prefix",
        ]
        up_process = subprocess.Popen(
            up_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        traceback_started = False
        error_capture = []

        # Capture container logs
        for line in up_process.stdout:
            print(line, end="")
            logs_buffer.append(line)

            if re.match(r'\s*File\s+".+",\s+line\s+\d+', line):
                traceback_started = True
                error_capture.append(line)
            elif traceback_started:
                error_capture.append(line)
            elif "Traceback" in line or "SyntaxError" in line:
                traceback_started = True
                error_capture.append(line)

            if "exited with code" in line:
                error_output = "".join(error_capture)
                break

        up_process.wait()
        if up_process.returncode != 0:
            raise Exception("Docker container execution failed")

        # No errors encountered
        state["proceed"] = "continue"

    except Exception as e:
        # On error, store details in state["error"]
        error_details = f"An error occurred: {e}"
        if error_output.strip():
            error_details += f"\n{error_output.strip()}"
        print(error_details)

        state["error"] = ErrorMessage(
            type="Docker Execution Error",
            details=error_details,
        )
        state["proceed"] = "fix"

    finally:
        print("Cleaning up Docker resources...")
        subprocess.run(["docker-compose", "down"])
        subprocess.run(["docker", "image", "prune", "-f"])
        os.chdir("..")

        # Append all logs to state["messages"]
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(
            {
                "role": "system",
                "content": "Docker Logs:\n" + "".join(logs_buffer)
            }
        )

    return state
