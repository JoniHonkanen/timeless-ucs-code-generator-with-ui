import os
from schemas import GraphState

# Save generated code to file
def write_code_to_file_agent(state: GraphState):
    print("\n**WRITE CODE TO FILE**")

    for code in state["codes"].codes:
        if code.executable_code:
            state["executable_file_name"] = code.filename

        full_file_path = os.path.join("generated/src", code.filename)
        directory = os.path.dirname(full_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        formatted_code = code.code.replace("\\n", "\n")
        with open(full_file_path, "w") as f:
            f.write(formatted_code)

    return state