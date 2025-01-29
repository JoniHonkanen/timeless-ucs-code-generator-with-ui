import os
import re
import time
import asyncio
import docker

from typing import List, Optional
from pydantic import BaseModel
from schemas import Code, Codes, DockerFiles, ErrorMessage  # Adjust import paths as needed
from .common import  llm, llm_code, PydanticOutputParser
from prompts.prompts import (
    CODE_FIXER_PROMPT,
    CODE_FIXER_AGENT_PROMPT,
    DEBUG_DOCKER_FILES_AGENT_PROMPT,
)
from schemas import CodeFix, DockerFile  # Adjust import paths as needed


async def debugging_agent(state):
    """
    A single agent that monitors container logs, fixes Dockerfiles, and fixes Python code.

    Relevant state fields:
    - state["error"] (ErrorMessage)
    - state["docker_files"] (DockerFiles)
    - state["docker_container_name"] (str)
    - state["codes"] (Codes)
    - state["messages"] (List)
    - state["code"] (Code)
    - state["iterations"] (int)
    - state["docker_output"] (str)  # If present, used for code fixing
    """

    print("*** MERGED DEBUGGING AGENT ***")
    container_name = state.get("docker_container_name", "")
    error_obj = state.get("error", None)
    docker_files = state.get("docker_files", None)
    code_collection = state.get("codes", None)
    single_code_obj = state.get("code", None)
    docker_output = state.get("docker_output", "")
    state.setdefault("iterations", 0)

    # 1) Monitor Docker container logs
    if container_name:
        new_error = await monitor_container_logs(container_name)
        if new_error:
            state["error"] = new_error
            # Append to docker_output so code can use it
            state["docker_output"] = (docker_output + f"\n{new_error.details}").strip()
            print("Container log error detected.")

    # 2) If we have a Docker error and docker_files, fix them
    if state.get("error") and docker_files:
        print("Attempting to fix Docker configuration...")
        try:
            await fix_docker_files(state)
            state["iterations"] += 1
        except Exception as e:
            update_error_state(state, f"Docker file fix error: {e}")
            return state

    # 3) If we have single_code_obj, fix code using new approach
    if single_code_obj:
        print("Fixing code using the new code logic...")
        try:
            new_code = await fix_code_logic(single_code_obj, state.get("docker_output", ""))
            updated_code = Code(
                python_code=new_code.fixed_python_code,
                requirements=new_code.requirements,
                resources=single_code_obj.resources,
            )
            state["code"] = updated_code

            with open("generated/generated.py", "w", encoding="utf-8") as f:
                f.write(updated_code.python_code)

            if new_code.requirements_changed:
                with open("generated/requirements.txt", "w", encoding="utf-8") as f:
                    f.write(new_code.requirements)

            state["iterations"] += 1
        except Exception as e:
            update_error_state(state, f"New code fix logic error: {e}")
            return state

    # 4) If we have code_collection (old style fix), handle that
    if code_collection and hasattr(code_collection, "codes"):
        print("Fixing code using old debug approach...")
        try:
            structured_llm = llm.with_structured_output(Code)
            prompt = CODE_FIXER_AGENT_PROMPT.format(
                original_code=code_collection.codes,
                error_message=state.get("error", ""),
            )
            fixed_code = structured_llm.invoke(prompt)

            for c in code_collection.codes:
                if c.filename == fixed_code.filename:
                    c.description = fixed_code.description
                    c.code = fixed_code.code
                    break

            state["codes"] = code_collection
            state["iterations"] += 1

            path = os.path.join("generated", fixed_code.filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(fixed_code.code.replace("\\n", "\n"))

        except Exception as e:
            update_error_state(state, f"Old style code fix error: {e}")
            return state

    # If no further errors, we continue
    state["proceed"] = "continue"
    return state


async def monitor_container_logs(container_name: str, check_interval=1, monitor_duration=3):
    """
    Monitors Docker container logs for 'monitor_duration' seconds.
    Returns an ErrorMessage if an error is detected, or None otherwise.
    """
    client = docker.from_env()
    start_time = time.time()
    try:
        container = client.containers.get(container_name)
        print(f"Monitoring container logs for '{container_name}' for {monitor_duration}s.")
        while True:
            if time.time() - start_time >= monitor_duration:
                print(f"No critical errors found after {monitor_duration}s.")
                break
            try:
                logs = container.logs(tail=20).decode("utf-8", errors="ignore")
                if "Traceback" in logs or "Error" in logs or re.search(r"File .+, line \d+", logs):
                    return ErrorMessage(type="Docker Execution Error", details=logs)
            except Exception as e:
                return ErrorMessage(type="Internal Code Error", details=str(e))
            await asyncio.sleep(check_interval)
    except docker.errors.NotFound:
        msg = f"Container '{container_name}' not found."
        return ErrorMessage(type="Container Not Found", details=msg)
    except Exception as e:
        msg = f"Unhandled error during log monitoring: {str(e)}"
        return ErrorMessage(type="Internal Code Error", details=msg)
    return None


async def fix_docker_files(state):
    """
    Fixes Dockerfiles using old debug_docker_execution_agent logic.
    """
    if not state.get("error") or not state.get("docker_files"):
        raise ValueError("Docker fix requires both state['error'] and state['docker_files'].")

    docker_files = state["docker_files"]
    error_obj = state["error"]
    messages = state.get("messages", [])
    structured_llm = llm.with_structured_output(DockerFile)

    prompt = DEBUG_DOCKER_FILES_AGENT_PROMPT.format(
        dockerfile=docker_files.dockerfile,
        docker_compose=docker_files.docker_compose,
        error_messages=error_obj.details,
        messages=messages,
    )
    result = structured_llm.invoke(prompt)

    docker_path = "generated"
    os.makedirs(docker_path, exist_ok=True)

    with open(os.path.join(docker_path, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write(result.dockerfile)
    with open(os.path.join(docker_path, "compose.yaml"), "w", encoding="utf-8") as f:
        f.write(result.docker_compose)

    state["docker_files"].dockerfile = result.dockerfile
    state["docker_files"].docker_compose = result.docker_compose


async def fix_code_logic(code: Code, docker_output: str) -> CodeFix:
    """
    Uses CODE_FIXER_PROMPT and the PydanticOutputParser to fix Python code 
    based on docker_output error details.
    """
    prompt = CODE_FIXER_PROMPT.format(
        code=code.python_code,
        requirements=code.requirements,
        resources=code.resources,
        docker_output=docker_output,
    )
    output_parser = PydanticOutputParser(pydantic_object=CodeFix)
    prompt += f"\n\n{output_parser.get_format_instructions()}"

    response_text = ""
    try:
        async for chunk in llm_code.astream(prompt):
            if hasattr(chunk, "content"):
                response_text += chunk.content
    except Exception as e:
        raise RuntimeError(f"Error during code generation: {e}")

    try:
        return output_parser.parse(response_text)
    except Exception as e:
        raise ValueError(f"Error parsing code response: {e}")


def update_error_state(state, message: str):
    """
    Appends the given message to 'docker_output' and sets 'error' to an ErrorMessage.
    """
    print(message)
    if "docker_output" not in state:
        state["docker_output"] = message
    else:
        state["docker_output"] += f"\n{message}"

    state["error"] = ErrorMessage(type="Debugging Error", details=message)
    state["proceed"] = "fix"
