import streamlit as st
from ollama import Client
from duckduckgo_search import DDGS

# Initialize Ollama client
ollama = Client(host='http://localhost:11434')

# Set page title and layout
st.title("Open-Source Local GPT with Web Search")
st.write("Powered by Streamlit, Ollama, and DuckDuckGo - Ask me anything!")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to perform web search
def web_search(query, max_results=3):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    # Combine search results into a single string
    context = "\n".join([f"{r['title']}: {r['body']}" for r in results])
    return context if context else "No relevant results found."

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Perform web search to get up-to-date context
    with st.spinner("Searching the web..."):
        search_context = web_search(prompt)
    
    # Combine user prompt with search context
    full_prompt = f"User question: {prompt}\nWeb search context: {search_context}\nAnswer based on the context or your knowledge if context is insufficient."

    # Get response from Ollama
    with st.chat_message("assistant"):
        response = ""
        placeholder = st.empty()
        for chunk in ollama.chat(model="llama3", messages=[
            {"role": "user", "content": full_prompt}
        ], stream=True):
            response += chunk['message']['content']
            placeholder.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})