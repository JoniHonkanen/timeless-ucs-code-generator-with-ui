import os
import asyncio
import time
import docker
from schemas import GraphState, ErrorMessage

async def log_docker_container_errors(state: GraphState):
    print("\n** LOG DOCKER CONTAINER ERRORS AGENT **")
    container_name = state["docker_container_name"]
    client = docker.from_env()
    error = None
    check_interval = 1
    monitor_duration = 3
    start_time = time.time()

    try:
        container = client.containers.get(container_name)
        print(
            f"Monitoring logs for container: {container_name} for {monitor_duration} seconds."
        )

        while True:
            try:
                logs = container.logs(tail=20).decode("utf-8")
                print("\nContainer Logs:\n", logs)
                error_message = parse_error_from_logs(logs)
                if error_message:
                    print(f"Error detected: {error_message.details}")
                    error = error_message
                    break

                print("No critical errors detected in the logs.")
                elapsed_time = time.time() - start_time
                if elapsed_time >= monitor_duration:
                    print(f"No errors detected after {monitor_duration} seconds.")
                    error = None
                    break

            except Exception as e:
                print(f"Failed to retrieve logs or process container: {e}")
                error = ErrorMessage(type="Internal Code Error", details=str(e))
                break

            await asyncio.sleep(check_interval)

    except docker.errors.NotFound:
        print(f"Error: Container '{container_name}' not found.")
        error = ErrorMessage(
            type="Container Not Found",
            details=f"Container '{container_name}' not found.",
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        error = ErrorMessage(type="Internal Code Error", details=str(e))

    return {"error": error}


def parse_error_from_logs(logs: str) -> ErrorMessage:
    error_type = "Execution Error"
    critical_error_keywords = [
        "traceback",
        "exception",
        "failed",
        "critical",
        "syntaxerror",
    ]

    error_lines = [
        line
        for line in logs.splitlines()
        if any(keyword in line.lower() for keyword in critical_error_keywords)
    ]

    if error_lines:
        error_details = "\n".join(error_lines)
        return ErrorMessage(type=error_type, details=error_details)

    return None
