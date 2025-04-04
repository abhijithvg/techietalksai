import streamlit as st
import requests
import os

# Get Model Runner URL from environment variable
MODEL_RUNNER_URL = os.getenv("MODEL_RUNNER_URL", "http://localhost:80")

st.title("LLM Chat Interface with Docker Model Runner")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to ask?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get response from Model Runner
    try:
        # Using OpenAI-compatible API endpoint provided by Model Runner
        response = requests.post(
            # f"{MODEL_RUNNER_URL}/engines/llama.cpp/v1/chat/completions",
            f"{MODEL_RUNNER_URL}/engines/v1/chat/completions",
            json={
                "model": "ai/llama3.2:latest",  # Example model, can be changed
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100
            }
        )
        response.raise_for_status()
        bot_response = response.json()["choices"][0]["message"]["content"]
        
        # Display bot response
        with st.chat_message("assistant"):
            st.markdown(bot_response)
        
        # Add to history
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with Model Runner: {str(e)}")
