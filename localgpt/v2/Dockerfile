# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
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

# Expose Streamlit port
EXPOSE 8502

# Start Ollama and run Streamlit
CMD bash -c "ollama serve & sleep 5 && ollama pull llama3 && streamlit run app.py --server.port 8502 --server.address 0.0.0.0"