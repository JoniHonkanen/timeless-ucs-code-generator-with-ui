import os
from .common import llm
from schemas import GraphState, Documentation, Code
from prompts.prompts import README_DEVELOPER_WRITER_AGENT_PROMPT
from typing import List


async def read_me_agent(state: GraphState):
    print("\n **GENERATING README & DEVELOPER FILES **")
    structured_llm = llm.with_structured_output(Documentation)
    code_descriptions = generate_code_descriptions(state["codes"].codes)
    prompt = README_DEVELOPER_WRITER_AGENT_PROMPT.format(
        messages=state["messages"], code_descriptions=code_descriptions
    )

    docs = structured_llm.invoke(prompt)
    readme = docs.readme
    developer = docs.developer

    # Define directory and ensure it exists
    base_dir = os.path.abspath("generated/src")  
    os.makedirs(base_dir, exist_ok=True)

    readme_path = os.path.join(base_dir, "README.md")
    developer_path = os.path.join(base_dir, "DEVELOPER.md")

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    with open(developer_path, "w", encoding="utf-8") as f:
        f.write(developer)

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
