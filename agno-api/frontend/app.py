import streamlit as st
import requests
import sseclient
import os

st.title("NYC News Reporter")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
prompt = st.text_input("Ask the reporter for a news story (e.g., 'What’s happening in Times Square?')")

# API call to backend
API_KEY = os.getenv("API_KEY", "my-super-secret-key-123")
BACKEND_URL = "http://backend:8000/news"

if prompt:
    with st.spinner("🚨 Chasing down the story... (this might take 30 seconds)"):
        url = f"{BACKEND_URL}?prompt={prompt}"
        headers = {"X-API-Key": API_KEY}
        
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()

            # Stream the response
            client = sseclient.SSEClient(response)
            response_text = ""
            text_placeholder = st.empty()

            for event in client.events():
                if event.data and event.data != "[DONE]":  # Skip empty or end signals
                    response_text += event.data
                    text_placeholder.markdown(response_text + "▌")
                    # st.write(f"DEBUG: Chunk received: {event.data}")  # Debug output

            text_placeholder.markdown(response_text)  # Final output without cursor
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching news: {e}")