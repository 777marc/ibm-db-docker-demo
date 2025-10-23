FROM python:3.11-slim

WORKDIR /app

# Install build deps for ibm_db - keep minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PORT=5000

CMD ["python", "app.py"]
