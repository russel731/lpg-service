FROM python:3.11-slim

WORKDIR /app

# 🔥 ВАЖНО — SSL и certs
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && update-ca-certificates

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]