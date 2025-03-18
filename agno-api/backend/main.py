from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from typing import Iterator
from agno.agent import Agent, RunResponse
from agno.models.ollama import Ollama
from agno.tools.duckduckgo import DuckDuckGoTools
from textwrap import dedent
from sse_starlette import EventSourceResponse
import logging
import os
from datetime import datetime

app = FastAPI()

# Secure API with an API key
API_KEY = os.getenv("API_KEY", "my-super-secret-key-123")
api_key_header = APIKeyHeader(name="X-API-Key")

# Setup logging
os.makedirs("../logs", exist_ok=True)
logging.basicConfig(
    filename="../logs/api_calls.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Dependency to validate API key
async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key

# Initialize the Agent
agent = Agent(
    model=Ollama(id="llama3.2", host="http://host.docker.internal:11434"),
    instructions=dedent("""\
        You are an enthusiastic news reporter with a flair for storytelling! 🗽
        Think of yourself as a mix between a witty comedian and a sharp journalist.

        Your style guide:
        - Start with an attention-grabbing headline using emoji
        - Share news with enthusiasm and NYC attitude
        - Keep your responses concise but entertaining
        - Throw in local references and NYC slang when appropriate
        - End with a catchy sign-off like 'Back to you in the studio!' or 'Reporting live from the Big Apple!'

        Remember to verify all facts and leverage Web search tool for real-time info when needed, while keeping that NYC energy high!\
    """),
    tools=[DuckDuckGoTools()],  # Rely on updated duckduckgo-search
    show_tool_calls=True,
    markdown=True,
)

# Streaming endpoint
@app.get("/news")
async def get_news(prompt: str, api_key: str = Depends(get_api_key)):
    # logger.info(f"Request - Prompt: {prompt}")
    
    def event_generator() -> Iterator[str]:
        run_response: Iterator[RunResponse] = agent.run(prompt, stream=True)
        full_response = ""
        for chunk in run_response:
            full_response += chunk.content
            yield chunk.content
        logger.info(f"Response - Prompt: {prompt} | Response: {full_response}")

    return EventSourceResponse(event_generator())

@app.on_event("startup")
async def startup_event():
    logger.info("Backend API started")