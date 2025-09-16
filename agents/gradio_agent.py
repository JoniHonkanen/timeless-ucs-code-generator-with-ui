import os
import shutil
import subprocess
from schemas import GraphState, ErrorMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the Gradio port (default to 7860 if not set)
gradio_port = os.getenv("GRADIO_PORT", "7860")

# Dynamically generate the frontend URL
frontend_url = f"http://localhost:{gradio_port}"

# Ultra-minimaalinen versio testauksen aloittamiseen
GRADIO_APP_CODE_ULTRA_MINIMAL = f"""
import gradio as gr

def greet(name):
    return "Hello " + (name or "World") + "!"

# Yksinkertainen Interface ilman mitään ekstraa
demo = gr.Interface(
    fn=greet,
    inputs="text",
    outputs="text"
)

demo.launch(server_name="0.0.0.0", server_port={gradio_port})
"""

# Gradio 5.45.0 -yhteensopiva täysi versio (korjattu)
GRADIO_APP_CODE = f"""
import gradio as gr
import tempfile
import zipfile
import os
import base64

def create_zip():
    try:
        code_folder = "/app/generated/src"
        if not os.path.exists(code_folder):
            print(f"Code folder does not exist: {{code_folder}}")
            return None
            
        # Tarkista onko kansiossa tiedostoja
        file_count = 0
        for root, dirs, files in os.walk(code_folder):
            file_count += len(files)
        
        if file_count == 0:
            print("No files found in code folder")
            return None
            
        zip_filename = "timeless.zip"
        zip_filepath = os.path.join(tempfile.gettempdir(), zip_filename)

        with zipfile.ZipFile(zip_filepath, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(code_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        relative_path = os.path.relpath(file_path, start=code_folder)
                        zf.write(file_path, arcname=relative_path)
                        print(f"Added to zip: {{relative_path}}")
        
        # Tarkista että zip luotiin onnistuneesti
        if os.path.exists(zip_filepath) and os.path.getsize(zip_filepath) > 0:
            print(f"ZIP created successfully: {{zip_filepath}} ({{os.path.getsize(zip_filepath)}} bytes)")
            return zip_filepath
        else:
            print("ZIP file creation failed")
            return None
            
    except Exception as e:
        print(f"Error creating zip: {{e}}")
        import traceback
        traceback.print_exc()
        return None

def read_file(filename):
    try:
        file_path = os.path.join("/app/generated/src", filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                return content if content.strip() else f"{{filename}} is empty."
        return f"{{filename}} not found."
    except Exception as e:
        return f"Error reading {{filename}}: {{str(e)}}"

def get_logo_html():
    logo_path = "/app/images/gptlab_sjk_logo.png"
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
                return f'''
                <div style="text-align: center; padding: 20px;">
                    <img src="data:image/png;base64,{{img_data}}" 
                         alt="GPT Lab Logo" 
                         style="max-width: 300px; max-height: 300px; object-fit: contain; border-radius: 8px;">
                </div>
                '''
        except Exception as e:
            return f'<div style="text-align: center; padding: 20px; color: red;">Error loading logo: {{e}}</div>'
    else:
        return '<div style="text-align: center; padding: 20px; color: gray;">Logo not found</div>'

# Gradio 5.45.0 modern syntax
with gr.Blocks(
    title="Timeless",
    theme=gr.themes.Soft()
) as demo:
    
    gr.Markdown("# TIMELESS")
    
    # Header row
    with gr.Row():
        with gr.Column(scale=1):
            # Logo - base64-encoded image
            logo_html = gr.HTML(get_logo_html())
        
        with gr.Column(scale=2):
            gr.Markdown("## Download the program source code")
            gr.Markdown("Click the button below to download all generated files as a ZIP package.")
            
            # Download section - yksinkertainen versio
            download_file = gr.File(
                label="Generated Code Package", 
                file_count="single",
                visible=True
            )
            download_btn = gr.Button(
                "Generate ZIP", 
                variant="primary", 
                size="lg"
            )
    
    gr.Markdown("---")
    gr.Markdown("### Documentation")
    
    # Documentation row
    with gr.Row():
        with gr.Column():
            readme_text = gr.Textbox(
                value=read_file("README.md"),
                label="README.md",
                lines=20,
                interactive=False,
                max_lines=30,
                show_copy_button=True
            )
        
        with gr.Column():
            dev_text = gr.Textbox(
                value=read_file("DEVELOPER.md"),
                label="DEVELOPER.md", 
                lines=20,
                interactive=False,
                max_lines=30,
                show_copy_button=True
            )

    # Yksinkertainen event handler - sama kuin alkuperäisessä toimivassa versiossa
    download_btn.click(
        fn=create_zip,
        outputs=download_file
    )

# Launch with modern parameters
demo.launch(
    server_name="0.0.0.0",
    server_port={gradio_port},
    show_error=True,
    quiet=False
)
"""

DOCKERFILE_CONTENT = f"""
FROM python:3.10-slim
WORKDIR /app

# Kopioi sovellustiedosto
COPY gradio_app.py .

# Asenna uusin Gradio
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir gradio==5.45.0

# Altistukset
EXPOSE {gradio_port}

# Käynnistys
CMD ["python", "-u", "gradio_app.py"]
"""

DOCKER_COMPOSE_CONTENT = f"""
version: '3.8'

services:
  gradio:
    container_name: ui-gradio-1
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "{gradio_port}:{gradio_port}"
    volumes:
      - ../../:/app/generated:ro
      - ../../../images/gptlab_sjk_logo.png:/app/images/gptlab_sjk_logo.png:ro
    environment:
      - PYTHONUNBUFFERED=1
      - GRADIO_SERVER_NAME=0.0.0.0
      - GRADIO_SERVER_PORT={gradio_port}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{gradio_port}"]
      interval: 30s
      timeout: 10s
      retries: 3
"""


async def start_gradio_frontend_agent(state: GraphState):
    print("*** STARTING GRADIO 5.45.0 FRONTEND ***")

    original_dir = os.getcwd()
    ui_dir = os.path.abspath("generated/src/ui")

    try:
        os.makedirs(ui_dir, exist_ok=True)
        os.chdir(ui_dir)

        # Tarkista onko kontaineri käynnissä
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=ui-gradio-1"],
            capture_output=True,
            text=True,
        )

        # Pysäytä vanha kontaineri jos on olemassa
        if result.stdout.strip():
            print("Stopping existing container...")
            try:
                subprocess.run(
                    ["docker", "compose", "down", "--remove-orphans"], check=True
                )
            except Exception:
                subprocess.run(
                    ["docker-compose", "down", "--remove-orphans"], check=True
                )

        print("Creating new Gradio 5.45.0 application...")

        # Luo tiedostot - käytä täyttä versiota
        with open("gradio_app.py", "w", encoding="utf-8") as f:
            f.write(GRADIO_APP_CODE)

        with open("Dockerfile", "w", encoding="utf-8") as f:
            f.write(DOCKERFILE_CONTENT)

        with open("docker-compose.yml", "w", encoding="utf-8") as f:
            f.write(DOCKER_COMPOSE_CONTENT)

        print("Starting container with full Gradio app...")

        # Käynnistä kontaineri
        try:
            subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True)
        except Exception:
            subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)

        print(f"Gradio frontend available at {frontend_url}")

        state["frontend_url"] = frontend_url

    except Exception as e:
        return {
            "error": ErrorMessage(
                type="Frontend Startup Error",
                message="Failed to start Gradio 5.45.0 frontend",
                details=str(e),
                code_reference="start_gradio_frontend_agent",
            )
        }

    finally:
        os.chdir(original_dir)

    return state
