from .common import llm_code
from schemas import GraphState, Codes
from prompts.prompts import CODE_GENERATOR_AGENT_PROMPT
from langchain_core.messages import AIMessage


# First step in graph flow
# -> Generate code based on user inputs
async def code_generator_agent(state: GraphState) -> GraphState:
    print("\n**CODE GENERATOR AGENT**")
    requirement = state["messages"][0].content
    prompt = CODE_GENERATOR_AGENT_PROMPT.format(requirement=requirement)
    structured_llm = llm_code.with_structured_output(Codes)

    generated_code = structured_llm.invoke(prompt)

    state["codes"] = generated_code
    state["messages"] += [AIMessage(content=f"{generated_code.description}")]

    for code in state["codes"].codes:
        state["messages"] += [
            AIMessage(
                content=f"Description of code: {code.description} \n"
                f"Programming language used: {code.programming_language} \n"
                f"{code.code}"
            )
        ]

    return state
