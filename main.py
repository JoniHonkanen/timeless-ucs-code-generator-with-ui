# RUN PROGRAM -> flask --app main run --no-reload
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
    debug_code_execution_agent,
    debug_docker_execution_agent,
    start_docker_container_agent,
    start_gradio_frontend_agent,
)
from schemas import GraphState

load_dotenv()
llm = get_openai_llm()

# Määritellään hakupolut
search_path = os.path.join(os.getcwd(), "generated")
file_path = os.path.join(search_path, "src")
test_file = os.path.join(search_path, "test")

# how many times we try to fix the error
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 3))

if not os.path.exists(search_path):
    os.mkdir(search_path)
    os.mkdir(os.path.join(search_path, "src"))
    os.mkdir(os.path.join(search_path, "test"))

workflow = StateGraph(GraphState)


def decide_to_end(state: GraphState):
    # Debugging function to decide which debugging approach to take
    # If no error -> Proceed to generate README files
    # If error in code -> debug_code
    # If error in Docker configuration -> debug_docker
    # If error something else -> debugger

    error_message = state["error"]

    if error_message:
        if state["iterations"] >= MAX_ITERATIONS:
            print("\nToo many iterations! Ending the process.")
            return "end"

        error_type = error_message.type

        if error_type == "Docker Configuration Error":
            return "debug_docker"
        elif error_type == "Docker Execution Error":
            return "debug_code"

        return "debugger"
    else:
        return "readme"


workflow.add_node("programmer", code_generator_agent)  # Create code files
workflow.add_node("saver", write_code_to_file_agent)  # Save code files
workflow.add_node("dockerizer", dockerizer_agent)  # Create Docker files (DockerF
workflow.add_node("executer_docker", start_docker_container_agent)  # Run code
workflow.add_node("debug_docker", debug_docker_execution_agent)  # Debug docker
workflow.add_node("debug_code", debug_code_execution_agent)  # Debug code
workflow.add_node("debugger", debug_code_agent)  # Debug something else
workflow.add_node("readme", read_me_agent)  # Create README # DEVELOPER files
workflow.add_node(
    "gradio_ui", start_gradio_frontend_agent
)  # create gradio UI for sharing the files

workflow.add_edge("programmer", "saver")
workflow.add_edge("saver", "dockerizer")
workflow.add_edge("dockerizer", "executer_docker")  # executer_docker -> conditional
workflow.add_edge("debugger", "saver")
workflow.add_edge("debug_docker", "executer_docker")
workflow.add_edge("debug_code", "executer_docker")
workflow.add_edge("readme", "gradio_ui")
workflow.add_edge("gradio_ui", END)

workflow.add_conditional_edges(
    source="executer_docker",
    path=decide_to_end,
    path_map={
        "readme": "readme",
        "debug_docker": "debug_docker",  # try to fix docker files
        "debug_code": "debug_code",  # try to fix file where error orccurs
        "debugger": "debugger",  # make all files again (this is final option if error)
        "end": END,  # end the process (if iterations full)
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

    try:
        # app.invoke muuttuu app.ainvoke, koska se on asynkroninen
        res = await app.ainvoke(
            {
                "messages": [HumanMessage(content=user_input)],
                "iterations": 0,
            },
            config=config,
        )
    except GraphRecursionError as e:
        print(f"GraphRecursionError: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "done!", "frontend_url": res.get("frontend_url", None)})


# Get Flask configurations from .env
flask_port = int(os.getenv("FLASK_PORT", 5000))

if __name__ == "__main__":
    flask_app.run(port=flask_port, debug=True, use_reloader=False)
