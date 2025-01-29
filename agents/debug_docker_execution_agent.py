import os
from .common import llm
from schemas import GraphState, DockerFile
from prompts.prompts import DEBUG_DOCKER_FILES_AGENT_PROMPT


async def debug_docker_execution_agent(state: GraphState):
    print("\n **DEBUG DOCKER AGENT**")
    error = state["error"]
    docker_files = state["docker_files"]
    dockerFile = docker_files.dockerfile
    dockerCompose = docker_files.docker_compose
    structured_llm = llm.with_structured_output(DockerFile)

    prompt = DEBUG_DOCKER_FILES_AGENT_PROMPT.format(
        dockerfile=dockerFile,
        docker_compose=dockerCompose,
        error_messages=error.details,
        messages=state["messages"],
    )
    fixed_docker_files = structured_llm.invoke(prompt)

    state["iterations"] += 1

    dockerfile_path = os.path.join("generated/src", "Dockerfile")
    docker_compose_path = os.path.join("generated/src", "compose.yaml")
    with open(dockerfile_path, "w", encoding="utf-8") as f:
        f.write(fixed_docker_files.dockerfile)
    with open(docker_compose_path, "w", encoding="utf-8") as f:
        f.write(fixed_docker_files.docker_compose)
    return state
