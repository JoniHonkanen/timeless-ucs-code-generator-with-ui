import os
from .common import llm
from schemas import GraphState, Code
from prompts.prompts import CODE_FIXER_AGENT_PROMPT


async def debug_code_execution_agent(state: GraphState):
    print("\n **DEBUG CODE**")
    error = state["error"]
    code_list = state["codes"].codes
    structured_llm = llm.with_structured_output(Code)

    prompt = CODE_FIXER_AGENT_PROMPT.format(
        original_code=code_list, error_message=error
    )
    fixed_code = structured_llm.invoke(prompt)

    print("\nOriginal Codes, one should be replaced:", code_list)
    print("\nNew Fixed Code:", fixed_code)
    print("\n\nAbove is the code to be updated.")

    for code in code_list:
        if code.filename == fixed_code.filename:
            code.description = fixed_code.description
            code.code = fixed_code.code
            break

    state["codes"].codes = code_list
    state["iterations"] += 1

    full_file_path = os.path.join("generated/src", fixed_code.filename)
    formatted_code = fixed_code.code.replace("\\n", "\n")
    with open(full_file_path, "w") as f:
        f.write(formatted_code)

    return state
