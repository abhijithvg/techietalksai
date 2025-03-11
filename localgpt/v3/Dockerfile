# Use an official Python runtime as a parent image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies, including procps for pkill
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Pre-install the model during build
RUN ollama serve & sleep 5 && ollama pull llama3 && pkill ollama

# Copy files and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# Define a build argument for the port (default: 8503)
ARG PORT=8503

# Set an environment variable to use the build argument
ENV APP_PORT=$PORT

# Expose the port using the environment variable
EXPOSE $APP_PORT

# Start Ollama and run Streamlit without pulling
CMD bash -c "ollama serve & sleep 5 && streamlit run app.py --server.port $APP_PORT --server.address 0.0.0.0 --server.fileWatcherType poll"