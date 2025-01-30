import os
import shutil
import subprocess
from schemas import GraphState, ErrorMessage

GRADIO_APP_CODE = """\
import gradio as gr
import tempfile
import zipfile
import os

def create_zip():
    code_folder = "/app/generated/src"
    zip_filename = "timeless.zip"
    zip_filepath = os.path.join(tempfile.gettempdir(), zip_filename)

    with zipfile.ZipFile(zip_filepath, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(code_folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, start=code_folder)
                zf.write(file_path, arcname=relative_path)

    return zip_filepath  # Return file path for Gradio to serve

def read_file(filename):
    file_path = os.path.join("/app/generated/src", filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"{filename} not found."

with gr.Blocks(title="Timeless") as demo:
    gr.Markdown("# TIMELESS")
    # Row 1: Logo and Download Section (Equal height using min_height)
    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            gr.Image("/app/images/gptlab_sjk_logo.png", elem_id="logo", height=300)
        with gr.Column(scale=3):
            gr.Markdown("## Download the program source code by clicking the button.")
            file_output = gr.File(label="Download ZIP")
            gr.Button("Download Code").click(fn=create_zip, inputs=[], outputs=file_output)

    # Row 2: Documentation (README & DEVELOPER)
    with gr.Row():
        gr.Markdown("### Documentation")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Textbox(value=read_file("README.md"), lines=20, interactive=False, label="README.md", show_label=True)
        with gr.Column(scale=1):
            gr.Textbox(value=read_file("DEVELOPER.md"), lines=20, interactive=False, label="DEVELOPER.md", show_label=True)

demo.launch(server_name="0.0.0.0", server_port=7860)
"""

DOCKERFILE_CONTENT = """\
FROM python:3.9-slim
WORKDIR /app
COPY gradio_app.py .
RUN pip install gradio
CMD ["python", "gradio_app.py"]
"""

DOCKER_COMPOSE_CONTENT = """\
version: '3'
services:
  gradio:
    container_name: ui-gradio-1
    build: .
    ports:
      - "7860:7860"
    volumes:
      - ../../:/app/generated
      - ../../../images/gptlab_sjk_logo.png:/app/images/gptlab_sjk_logo.png
"""


async def start_gradio_frontend_agent(state: GraphState):
    print("*** STARTING / UPDATING GRADIO FRONTEND ***")

    original_dir = os.getcwd()
    ui_dir = os.path.abspath("generated/src/ui")
    generated_src_path = os.path.abspath("generated/src")

    try:
        os.makedirs(ui_dir, exist_ok=True)
        os.chdir(ui_dir)

        # Check if the Gradio container is already running
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=ui-gradio-1"], capture_output=True, text=True
        )

        if result.stdout.strip():
            print("Gradio container exists. Restarting...")
            # Ensure the correct path is used
            generated_src_path = os.path.abspath("generated/src")
            subprocess.run(
                ["docker", "cp", "../../.", "ui-gradio-1:/app/generated/"],
                check=True,
            )

            # Restart the container
            subprocess.run(["docker-compose", "restart", "gradio"], check=True)
        else:
            print("Gradio container not running. Starting fresh...")

            # Create necessary files for first-time run
            with open("gradio_app.py", "w", encoding="utf-8") as f:
                f.write(GRADIO_APP_CODE)

            with open("Dockerfile", "w", encoding="utf-8") as f:
                f.write(DOCKERFILE_CONTENT)

            with open("docker-compose.yml", "w", encoding="utf-8") as f:
                f.write(DOCKER_COMPOSE_CONTENT)

            # Start container without rebuilding
            subprocess.run(["docker-compose", "up", "-d"], check=True)

        # Delete local files after copying
        #print("POISTETAAN TIEDOSTOT!")
        #shutil.rmtree(generated_src_path, ignore_errors=True)
        #os.makedirs(generated_src_path, exist_ok=True)
        # Save frontend URL in the state
        frontend_url = "http://localhost:7860"
        state["frontend_url"] = frontend_url
        print(f"Gradio frontend is available at {frontend_url}")

    except Exception as e:
        return {
            "error": ErrorMessage(
                type="Frontend Startup Error",
                message="Failed to start or update Gradio frontend",
                details=str(e),
                code_reference="start_gradio_frontend_agent",
            )
        }

    finally:
        os.chdir(original_dir)

    return state
