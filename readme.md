# AI-Agent Powered Code Generation and Docker Setup

## Introduction

This project demonstrates the use of language models and AI agents to fully automate the process of generating code based on user input, setting up a Docker environment, and creating documentation for the project, including `README.md` and `developer.md` files. The AI agents collaborate to analyze the user’s request, generate the necessary code, configure Docker, and produce relevant documentation.

Each task in the workflow is handled by a specific agent. This includes analyzing the user's input, generating program code, setting up the required Docker environment, and finally ensuring that all project files, including code and documentation, are produced correctly. An additional agent manages error handling during Docker startup or code execution.

A new agent has been added to automate the Docker environment setup and allow users to download the generated code as a ZIP file through Gradio.

The main goal of the project is to explore the potential of language models and AI agents in automating the entire software development process, from code generation to deployment. By leveraging Docker, the generated programs can run across various programming languages in an isolated environment. Currently, the project supports small-scale program generation, but additional work is required for larger, more complex systems, particularly in areas such as code modularization and robust error handling.

This project was developed in Python and uses the OpenAI API to integrate large language models. We also employed LangChain and LangGraph for managing AI agent workflows, Flask for providing a REST API, and Gradio for allowing users to download the generated code.

### This is part of timeless project:
<img src="images/timeless_big_picture.png" alt="Timeless project" style="height: 300px; width: auto;">

## Features

- **Code Generation**: Based on user-provided input, AI agents generate fully functional program code.
- **Docker Environment Setup**: Automatically configures a Docker environment to run the generated code.
- **Automated Documentation**: AI agents generate documentation for the project, including `README.md`.
- **Error Handling**: Handles errors in Docker startup and code execution.
- **REST API Interface**: A Flask-based API allows users to interact with the system via HTTP requests.
- **Downloadable Code Packages**: Generated code is packaged as a ZIP file and can be downloaded via Gradio.
### Agents and edges:
<img src="images/graphs/graph_flow.png" alt="Work flow" style="height: 300px; width: auto;">

## Technologies Used

- **Python**: Core language for project development.
- **OpenAI API**: Provides the large language model for generating code and handling input.
- **LangChain**: Framework for integrating language models into the application.
- **LangGraph**: Manages workflows and interactions between AI agents.
- **Flask**: Provides a REST API for handling user requests.
- **Gradio**: Allows users to download the generated code as a ZIP package.
- **Docker**: Ensures that generated programs run in isolated environments.
### Different states of workflow:
<img src="images/timeless_code_generator-workflow.png" alt="GPT Lab Seinäjoki Logo" style="height: 350px; width: auto;">

## Installation

1. Start virtual environment:
   .venv\Scripts\activate  # Windows
2. install packages -> pip install -r requirements.txt
3. create .env file with own keys for openai
   1. OPENAI_API_KEY
4. create config.ini
   1. [LLM]
      model=gpt-4o-mini
5. run program -> python main.py


## Future Improvements

- Improve code modularization for larger projects.
- Enhance error checking and handling capabilities.
- Expand support for additional programming languages and frameworks.
- Deploy UI to cloud
- Better gradio... 


### Flask API

The system provides a REST API accessible via HTTP. Users can send requests to generate code by making a `POST` request to:
http://127.0.0.1:5000/prompt

### Example JSON Request

To send a request to the Flask API, use the following JSON structure:

```json
{
    "input": "Make example program with python with multiple files"
}
```

# GPT Lab Seinäjoki

**This project under the GPT Lab Seinäjoki program supports the regional strategy of fostering an innovative ecosystem and advancing smart, skilled development. Its goal is to introduce new AI knowledge and technology to the region, enhance research and innovation activities, and improve business productivity.**

<img src="images/gptlab_sjk_logo.png" alt="GPT Lab Seinäjoki Logo" style="height: 180px; width: auto;">

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.










