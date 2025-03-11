import streamlit as st
from ollama import Client

# Initialize Ollama client
ollama = Client(host='http://localhost:11434')

# Set page title and layout
st.title("Open-Source Local GPT")
st.write("Powered by Streamlit and Ollama - Ask me anything!")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from Ollama
    with st.chat_message("assistant"):
        # Stream the response
        response = ""
        placeholder = st.empty()
        for chunk in ollama.chat(model="llama3", messages=[
            {"role": "user", "content": prompt}
        ], stream=True):
            response += chunk['message']['content']
            placeholder.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})