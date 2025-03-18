FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8502

ENTRYPOINT ["streamlit", "run", "--server.port=8502", "--server.address=0.0.0.0"]
CMD ["app.py"]