from .common import llm
from schemas import GraphState, Codes
from prompts.prompts import CODE_FIXER_AGENT_PROMPT
from langchain_core.messages import AIMessage


# Debug codes if error occurs
async def debug_code_agent(state: GraphState):
    print("\n **DEBUG CODE**")
    error = state["error"]
    code = state["codes"].codes
    structured_llm = llm.with_structured_output(Codes)
    prompt = CODE_FIXER_AGENT_PROMPT.format(original_code=code, error_message=error)
    fixed_code = structured_llm.invoke(prompt)

    state["codes"] = fixed_code

    for code in state["codes"].codes:
        state["messages"] += [
            AIMessage(
                content=f"Description of code: {code.description} \n"
                f"Programming language used: {code.programming_language} \n"
                f"{code.code}"
            )
        ]

    state["iterations"] += 1

    return state
