FROM selenium/standalone-chrome:latest

USER root

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libxss1 \
    libappindicator1 \
    libindicator7 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libgconf-2-4 \
    libfontconfig1 \
    libnss3 \
    libxdamage1 \
    libxtst6 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY streamlit_app_local.py app.py
COPY .streamlit/ .streamlit/

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
