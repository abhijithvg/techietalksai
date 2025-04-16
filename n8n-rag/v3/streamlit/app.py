import streamlit as st
import requests
import os
import uuid

# Configuration
# N8N_BASE_URL = "http://n8n-auto:5678"  # Update if n8n is on a different host
N8N_BASE_URL = f"https://{NGROK_STATIC_URL}"  # Update if n8n is on a different host
IMPORT_WORKFLOW_ID = "1ea01307-31b7-44e1-9d74-cf4c63631767"  # Get from n8n workflow URL
QUERY_WORKFLOW_ID = "644a955c-d357-41e6-a895-e6355fcc6b0f"    # Get from n8n workflow URL

# N8N_PATH = "webhook-test"
N8N_PATH = "webhook"

# Helper functions
def upload_to_qdrant(file: bytes, filename: str, collection: str) -> dict:
    """Send file to n8n for processing and Qdrant storage"""
    url = f"{N8N_BASE_URL}/{N8N_PATH}/{IMPORT_WORKFLOW_ID}"
    # Explicitly set MIME type based on file extension
    mime_type = "application/octet-stream"  # Default binary
    if filename.endswith('.csv'):
        mime_type = "text/csv"
    elif filename.endswith('.pdf'):
        mime_type = "application/pdf"
    elif filename.endswith('.txt'):
        mime_type = "text/plain"
    elif filename.endswith('.docx'):
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    files = {'file': (filename, file, mime_type)}
    data = {'collection': collection}
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status_code": getattr(e.response, "status_code", None)}

def query_qdrant(query: str, collection: str, limit: int = 5) -> dict:
    """Query Qdrant via n8n workflow"""
    url = f"{N8N_BASE_URL}/{N8N_PATH}/{QUERY_WORKFLOW_ID}"
    params = {
        'query': query,
        'collection': collection,
        'limit': limit
    }
    
    response = requests.get(url, params=params)
    return response.json()

# Streamlit UI
st.title("Qdrant Vector Store Manager")

# Tab layout
upload_tab, query_tab = st.tabs(["Upload Documents", "Query Vector Store"])

with upload_tab:
    st.header("Upload Documents to Qdrant")
    
    with st.form("upload_form"):
        collection = st.text_input("Collection Name", value="wonders_of_world")
        uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'docx', 'csv'])
        submit_button = st.form_submit_button("Upload")
        
        if submit_button and uploaded_file is not None:
            with st.spinner("Processing file..."):
                result = upload_to_qdrant(
                    file=uploaded_file.getvalue(),
                    filename=uploaded_file.name,
                    collection=collection
                )
                
            if result.get('success'):
                st.success("File successfully uploaded to Qdrant!")
                st.json(result)
            else:
                st.error("Error uploading file")
                st.json(result)

with query_tab:
    st.header("Query Qdrant Vector Store")
    
    with st.form("query_form"):
        collection = st.text_input("Collection Name", value="wonders_of_world", key="query_collection")
        query_text = st.text_area("Enter your query")
        limit = st.number_input("Results limit", min_value=1, max_value=20, value=5)
        submit_button = st.form_submit_button("Search")
        
        if submit_button and query_text:
            with st.spinner("Searching..."):
                results = query_qdrant(
                    query=query_text,
                    collection=collection,
                    limit=limit
                )
                
            if isinstance(results, list):
                # Handle case where results are a list (e.g., multiple matches)
                st.success(f"Found {len(results)} results")
                for idx, result in enumerate(results, 1):
                    try:
                        if isinstance(result, str):
                            result = json.loads(result)
                        with st.expander(f"Result {idx}"):
                            if isinstance(result, dict):
                                score = result.get('score', 0)
                                st.caption(f"Score: {score:.2f}")
                                content = result.get('payload', {}).get('content', 'No content')
                                st.write(content)
                                st.json(result)
                            else:
                                st.write(result)
                    except Exception as e:
                        st.error(f"Error displaying result: {str(e)}")
                        st.write(result)
            elif isinstance(results, dict):
                if results.get('error'):
                    # Handle error case
                    st.error(f"Query failed: {results['error']}")
                elif 'response' in results:
                    # Handle successful response with 'response' key
                    response = results['response']
                    st.success("Query successful!")
                    st.write(response.get('text', 'No text found'))
                    st.json(results)
                else:
                    st.warning("Unexpected response format")
                    st.json(results)
            else:
                st.warning("No results found")
                st.json(results)