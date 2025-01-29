import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.pregel import GraphRecursionError

# own imports
from llm_models.openai_models import get_openai_llm
from agents import (
    code_generator_agent,
    write_code_to_file_agent,
    debug_code_agent,
    read_me_agent,
    dockerizer_agent,
    execute_docker_agent,
    debug_code_execution_agent,
    debug_docker_execution_agent,
    log_docker_container_errors,
)
from schemas import GraphState

load_dotenv()
llm = get_openai_llm()

# Määritellään hakupolut
search_path = os.path.join(os.getcwd(), "generated")
file_path = os.path.join(search_path, "src")
test_file = os.path.join(search_path, "test")

if not os.path.exists(search_path):
    os.mkdir(search_path)
    os.mkdir(os.path.join(search_path, "src"))
    os.mkdir(os.path.join(search_path, "test"))

workflow = StateGraph(GraphState)


""" async def create_code_f(state: GraphState):
    print("ENTERING CREATE CODE FUNCTION")
    return await code_generator_agent(state, llm) """


# def write_code_to_file_f(state: GraphState):
#    return write_code_to_file_agent(state, file_path)


""" async def execute_code_f(state: GraphState):
    return await execute_code_agent(state, file_path) """


""" async def execute_docker_f(state: GraphState):
    return await execute_docker_agent(state, file_path) """


""" async def debug_code_f(state: GraphState):
    return await debug_code_agent(state, llm) """


""" async def debug_docker_f(state: GraphState):
    return await debug_docker_execution_agent(state, llm, file_path) """


""" async def debug_code_docker_f(state: GraphState):
    return await debug_code_execution_agent(state, llm, file_path) """


""" async def log_docker_errors_f(state: GraphState):
    return await log_docker_container_errors(state) """


""" async def read_me_f(state: GraphState):
    return await read_me_agent(state, llm, file_path) """


""" async def dockerize_f(state: GraphState):
    return await dockerizer_agent(state, llm, file_path) """


def decide_to_end(state: GraphState):
    print("\nENTERING DECIDE TO END FUNCTION")
    print(f"iterations: {state['iterations']}")
    print(f"error: {state['error']}")

    error_message = state["error"]

    if error_message:
        if state["iterations"] >= 3:
            print("\nToo many iterations! Ending the process.")
            return "end"

        error_type = error_message.type
        print("Deciding which debugging approach to take")

        if error_type == "Docker Configuration Error":
            return "debug_docker"
        elif error_type == "Docker Execution Error":
            return "debug_code"

        return "debugger"
    else:
        return "readme"


workflow.add_node("programmer", code_generator_agent)
workflow.add_node("saver", write_code_to_file_agent)
workflow.add_node("dockerizer", dockerizer_agent)
workflow.add_node("executer_docker", execute_docker_agent)
workflow.add_node("debugger", debug_code_agent)
workflow.add_node("debug_docker", debug_docker_execution_agent)
workflow.add_node("debug_code", debug_code_execution_agent)
workflow.add_node("log_docker_errors", log_docker_container_errors)
workflow.add_node("readme", read_me_agent)

workflow.add_edge("programmer", "saver")
workflow.add_edge("saver", "dockerizer")
workflow.add_edge("dockerizer", "executer_docker")
workflow.add_edge("debugger", "saver")
workflow.add_edge("debug_docker", "executer_docker")
workflow.add_edge("debug_code", "log_docker_errors")
workflow.add_edge("readme", END)

workflow.add_conditional_edges(
    source="executer_docker",
    path=decide_to_end,
    path_map={
        "readme": "readme",
        "debugger": "debugger",
        "debug_docker": "debug_docker",
        "debug_code": "debug_code",
        "end": END,
    },
)
workflow.add_conditional_edges(
    source="log_docker_errors",
    path=decide_to_end,
    path_map={
        "readme": "readme",
        "debugger": "debugger",
        "debug_docker": "debug_docker",
        "debug_code": "debug_code",
        "end": END,
    },
)

workflow.set_entry_point("programmer")
app = workflow.compile()
app.get_graph().draw_mermaid_png(output_file_path="images/graphs/graph_flow.png")

flask_app = Flask(__name__)


@flask_app.route("/prompt", methods=["POST"])
async def main():
    user_input = request.json.get("prompt", "")
    print(f"User input: {user_input}")
    config = RunnableConfig(recursion_limit=20)
    print("NYT LÄHTEE!")

    try:
        # app.invoke muuttuu app.ainvoke, koska se on asynkroninen
        results = await app.ainvoke(
            {
                "messages": [HumanMessage(content=user_input)],
                "iterations": 0,
            },
            config=config,
        )
    except GraphRecursionError as e:
        print(f"GraphRecursionError: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "done!", "results": results})


if __name__ == "__main__":
    flask_app.run(port=5000, debug=True)
