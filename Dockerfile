FROM python:3.11-slim

# Install chromium and dependencies
RUN apt-get update && apt-get install -y \
    chromium-browser \
    chromium-driver \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_app_local.py app.py
COPY .streamlit/ .streamlit/

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
