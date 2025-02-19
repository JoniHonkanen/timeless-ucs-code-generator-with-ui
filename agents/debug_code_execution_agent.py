import os
import re
from .common import llm
from schemas import GraphState, Code
from prompts.prompts import CODE_FIXER_AGENT_PROMPT

#with done update we want only append the code that need to be fixed to prompt

async def debug_code_execution_agent(state: GraphState):
    print("\n **DEBUG CODE EXECUTION AGENT**")
    error = state["error"]
    code_list = state["codes"].codes
    structured_llm = llm.with_structured_output(Code)

    # Since the code is executed in a Docker environment, error messages always contain the '/app/' path.
    # Modify the regex to recognize any file extension (e.g., .py, .js, .java, etc.).
    error_details = error.details
    files_in_error = re.findall(r"/app/([^/]+\.\w+)", error_details)

    if files_in_error:
        # Filter the code list to include only the files mentioned in the error message.
        # This optimization prevents unnecessary processing of large, unrelated files.
        filtered_code_list = [
            code for code in code_list if code.filename in files_in_error
        ]
    else:
        # If no specific files are mentioned, process all files (fallback scenario).
        filtered_code_list = code_list

    # Format the prompt with only the relevant erroneous files to optimize performance.
    prompt = CODE_FIXER_AGENT_PROMPT.format(
        original_code=filtered_code_list, error_message=error
    )
    fixed_code = structured_llm.invoke(prompt)

    # Update only the corrected file while keeping other files unchanged.
    for code in code_list:
        if code.filename == fixed_code.filename:
            code.description = fixed_code.description
            code.code = fixed_code.code
            break

    # Store the updated code list back in the state and increment the iteration counter.
    state["codes"].codes = code_list
    state["iterations"] += 1

    # Write the fixed code to a file in the 'generated/src' directory.
    full_file_path = os.path.join("generated/src", fixed_code.filename)
    formatted_code = fixed_code.code.replace("\\n", "\n")
    with open(full_file_path, "w") as f:
        f.write(formatted_code)

    return state


# OLD ONE... before 19.2.2025
""" import os
from .common import llm
from schemas import GraphState, Code
from prompts.prompts import CODE_FIXER_AGENT_PROMPT


async def debug_code_execution_agent(state: GraphState):
    print("\n **DEBUG CODE EXECUTION AGENT**")
    error = state["error"]
    print("\n")
    print(f"Error: {error}")
    code_list = state["codes"].codes
    print(f"Code: {code_list}")
    structured_llm = llm.with_structured_output(Code)

    prompt = CODE_FIXER_AGENT_PROMPT.format(
        original_code=code_list, error_message=error
    )
    fixed_code = structured_llm.invoke(prompt)
    print(f"Fixed code: {fixed_code}")

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

    return state """
