import streamlit as st
import os
from ollama import Client
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException
from datetime import datetime  # Added for time formatting

# Initialize Ollama client
ollama = Client(host='http://localhost:11434')

# Set page title and layout
st.title("Open-Source Local GPT with Web Search - v3a")
st.write("Powered by Streamlit and Ollama - Web search only when needed!")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history with source indicator
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Display source indicator if it's an assistant message
        if message["role"] == "assistant":
            source = message.get("source", "LLM Only")  # Default to LLM Only if not specified
            st.caption(f"Source: {source}")

# Function to perform web search
def web_search(query, max_results=3):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        context = "\n".join([f"{r['title']}: {r['body']}" for r in results])
        return context if context else "No relevant results found."
    except RatelimitException:
        return "Web search unavailable due to rate limits."

# Function to check if response indicates uncertainty or outdated info
def is_uncertain(prompt, llm_response):
    current_year = datetime.now().year
    meta_prompt = f"Today is {current_year}. Given the question '{prompt}' and the response '{llm_response}', does this require information beyond your knowledge cutoff date? Answer with 'Yes' or 'No' only."
    meta_response = ""
    for chunk in ollama.chat(model="llama3", messages=[
        {"role": "user", "content": meta_prompt}
    ], stream=True):
        meta_response += chunk['message']['content']
    return "yes" in meta_response.lower()

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get initial response from Ollama
    with st.chat_message("assistant"):
        placeholder = st.empty()
        initial_response = ""
        for chunk in ollama.chat(model="llama3", messages=[
            {"role": "user", "content": prompt}
        ], stream=True):
            initial_response += chunk['message']['content']
            placeholder.markdown(initial_response)

        # Check if the initial response is uncertain
        if is_uncertain(prompt, initial_response):
            with st.spinner("Local knowledge insufficient, searching the web..."):
                # Perform web search for additional context
                search_context = web_search(prompt)
                full_prompt = f"User question: {prompt}\nWeb search context: {search_context}\nAnswer based on the context or your knowledge if context is sufficient."
                
                # Get updated response with web context
                response = ""
                if "rate limits" in search_context:
                    response = initial_response + "\n(Note: Web search failed due to rate limits.)"
                    source = "LLM + Web Search (Failed)"
                else:
                    for chunk in ollama.chat(model="llama3", messages=[
                        {"role": "user", "content": full_prompt}
                    ], stream=True):
                        response += chunk['message']['content']
                    source = "LLM + Web Search"
                # Update placeholder with final response and source
                # placeholder.markdown(f"{response}\n\n*Source: {source}*")
                # Display response and source as caption
                placeholder.markdown(response)
                st.caption(f"Source: {source}")
                st.session_state.messages.append({"role": "assistant", "content": response, "source": source})
        else:
            # Use the initial response if it seems confident
            source = "LLM Only"
            # placeholder.markdown(f"{initial_response}\n\n*Source: {source}*")
            # Display response and source as caption
            placeholder.markdown(initial_response)
            st.caption(f"Source: {source}")
            st.session_state.messages.append({"role": "assistant", "content": initial_response, "source": source})