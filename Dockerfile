FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web.py .

EXPOSE 10000

CMD ["streamlit", "run", "web.py", "--server.port=10000", "--server.address=0.0.0.0"]
