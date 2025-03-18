import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, time
import os

st.title("API Call Log Viewer")

# Path to log file
LOG_FILE = "/logs/api_calls.log"

def parse_logs(log_file):
    if not os.path.exists(log_file):
        return pd.DataFrame(columns=["timestamp", "type", "prompt", "response"])
    
    data = []
    current_response = ""
    prev_timestamp = None
    prev_type = None
    prev_prompt = None

    with open(log_file, "r") as f:
        for line in f:
            # Match timestamp and type for a new log entry
            timestamp_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (Request|Response|Backend API started) - ", line)
            if timestamp_match:
                # If we have a previous entry, save it before starting a new one
                if prev_timestamp is not None and prev_type in ["Request", "Response"]:
                    data.append({
                        "timestamp": datetime.strptime(prev_timestamp, "%Y-%m-%d %H:%M:%S,%f"),
                        "type": prev_type,
                        "prompt": prev_prompt,
                        "response": current_response.strip() if current_response else None
                    })

                # Reset for the new log entry
                current_response = ""
                prev_timestamp, prev_type = timestamp_match.groups()

                # Skip "Backend API started" entries for display
                if prev_type == "Backend API started":
                    prev_timestamp = None
                    prev_type = None
                    prev_prompt = None
                    continue

                # Extract prompt and response
                prompt_match = re.search(r"Prompt: (.*?)(?: \| Response: (.*))?$", line)
                if prompt_match:
                    prev_prompt = prompt_match.group(1).strip()
                    response = prompt_match.group(2)
                    if response:
                        current_response = response.strip()
                    else:
                        current_response = None
            elif prev_timestamp is not None and prev_type in ["Request", "Response"] and current_response is not None and line.strip():
                # Append to response only if we're in a Response entry and the line doesn't start with a timestamp
                if not re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}", line):
                    current_response += "\n" + line.strip()

        # Handle the last entry
        if prev_timestamp is not None and prev_type in ["Request", "Response"] and current_response:
            data.append({
                "timestamp": datetime.strptime(prev_timestamp, "%Y-%m-%d %H:%M:%S,%f"),
                "type": prev_type,
                "prompt": prev_prompt,
                "response": current_response.strip() if current_response else None
            })

    return pd.DataFrame(data)

# Load and display logs
df = parse_logs(LOG_FILE)

if df.empty:
    st.warning("No logs found yet. Make some API calls first!")
else:
    # Initialize session state for reset
    if "reset_trigger" not in st.session_state:
        st.session_state["reset_trigger"] = False

    # Sidebar for filters
    st.sidebar.header("Log Filters")
    
    # Date filter
    start_date = st.sidebar.date_input("Start Date", df["timestamp"].min().date(), key="start_date")
    end_date = st.sidebar.date_input("End Date", df["timestamp"].max().date(), key="end_date")
    
    # Time filter (side by side)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_time = st.time_input("Start Time", time(0, 0), key="start_time")
    with col2:
        end_time = st.time_input("End Time", time(23, 59), key="end_time")
    
    # Searchable prompt filter
    search_query = st.sidebar.text_input("Search Prompts", "", key="search_query")

    # Reset button with trigger
    if st.sidebar.button("Reset Filters"):
        st.session_state["reset_trigger"] = not st.session_state["reset_trigger"]
        st.rerun()  # Use st.rerun() instead of experimental_rerun

    # Apply reset if triggered
    if st.session_state["reset_trigger"]:
        start_date = df["timestamp"].min().date()
        end_date = df["timestamp"].max().date()
        start_time = time(0, 0)
        end_time = time(23, 59)
        search_query = ""  # Clear the search query
        st.session_state["reset_trigger"] = False

    # Apply date and time filters
    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)
    filtered_df = df[(df["timestamp"] >= start_datetime) & (df["timestamp"] <= end_datetime)]

    # Apply search filter
    if search_query:
        filtered_df = filtered_df[filtered_df["prompt"].str.contains(search_query, case=False, na=False)]

    # Raw log display with full text and search
    st.subheader("Raw Logs")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "response": st.column_config.TextColumn(
                "Response",
                width="large",
                help="Full response text"
            )
        }
    )

    # Request Frequency Over Time
    st.subheader("Request Frequency Over Time")
    freq_df = filtered_df[filtered_df["type"] == "Request"].groupby(filtered_df["timestamp"].dt.floor("5min")).size().reset_index(name="count")
    fig1 = px.line(freq_df, x="timestamp", y="count", title="Requests per 5-Minute Interval")
    st.plotly_chart(fig1)

    # Response Length Distribution
    st.subheader("Response Length Distribution")
    response_df = filtered_df[filtered_df["type"] == "Response"].copy()
    response_df["response_length"] = response_df["response"].str.len().fillna(0)
    fig2 = px.histogram(response_df, x="response_length", nbins=20, title="Distribution of Response Lengths")
    st.plotly_chart(fig2)

    # Prompt Word Cloud (simple text count)
    st.subheader("Most Common Words in Prompts")
    prompt_words = " ".join(filtered_df["prompt"].dropna()).split()
    word_freq = pd.Series(prompt_words).value_counts().head(10)
    fig3 = px.bar(word_freq, x=word_freq.index, y=word_freq.values, title="Top 10 Words in Prompts")
    st.plotly_chart(fig3)