import os
from .common import llm
from schemas import GraphState, DockerFile, DockerFiles, Code
from prompts.prompts import DOCKERFILE_GENERATOR_AGENT_PROMPT
from langchain_core.messages import AIMessage
from typing import List


async def dockerizer_agent(state: GraphState):
    print("\n **DOCKERIZER AGENT **")

    structured_llm = llm.with_structured_output(DockerFile)
    code_descriptions = generate_code_descriptions(state["codes"].codes)
    prompt = DOCKERFILE_GENERATOR_AGENT_PROMPT.format(
        executable_file_name=state["executable_file_name"],
        code_descriptions=code_descriptions,
        messages=state["messages"],
    )

    docker_things = structured_llm.invoke(prompt)
    docker_files_instance = DockerFiles(
        dockerfile=docker_things.dockerfile, docker_compose=docker_things.docker_compose
    )

    state["docker_files"] = docker_files_instance
    state["docker_image_name"] = docker_things.docker_image_name
    state["docker_container_name"] = docker_things.docker_container_name

    dockerfile_path = os.path.join("generated/src", "Dockerfile")
    docker_compose_path = os.path.join("generated/src", "compose.yaml")

    state["messages"] += [
        AIMessage(content=f"Description of dockerfile: {docker_things.description}"),
        AIMessage(content=f"Dockerfile: {docker_things.dockerfile}"),
        AIMessage(content=f"Docker.yaml: {docker_things.docker_compose}"),
        AIMessage(content=f"Docker image name: {docker_things.docker_image_name}"),
        AIMessage(
            content=f"Docker container name: {docker_things.docker_container_name}"
        ),
    ]

    with open(dockerfile_path, "w", encoding="utf-8") as f:
        f.write(docker_things.dockerfile)
    with open(docker_compose_path, "w", encoding="utf-8") as f:
        f.write(docker_things.docker_compose)

    return state


def generate_code_descriptions(codes: List[Code]) -> str:
    descriptions = []
    for code in codes:
        executable_note = "(Executable)" if code.executable_code else ""
        descriptions.append(
            f"**{code.filename}** {executable_note}\n"
            f"Language: {code.programming_language}\n"
            f"Description: {code.description}"
        )
    return "\n\n".join(descriptions)
