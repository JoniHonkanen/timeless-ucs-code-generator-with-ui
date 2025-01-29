# agents/common.py
# This file contains common objects and functions that can be shared across multiple agents or modules.
# Just for reducing redundacy
import os
from langchain.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables once
load_dotenv()

# Shared LLM instance
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")
llm_code = ChatOpenAI(api_key=api_key, model="gpt-4o")

# Export common objects or functions
__all__ = ["PydanticOutputParser", "llm", "llm_code"]
