# Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# install deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

# make your package importable
ENV PYTHONPATH=/app

# 💡 important: tell Prefect NOT to connect to an external API
ENV PREFECT_API_URL=""

# optional: silence event errors
ENV PREFECT_LOGGING_SERVER_EVENTS="false"

# run the orchestrator flow
CMD ["python", "-m", "src.orchestrator.flows"]
