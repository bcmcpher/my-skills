FROM python:3.12-slim

WORKDIR /app

COPY run_server.py pyproject.toml ./

RUN pip install --no-cache-dir "mcp[cli]>=1.0"

CMD ["python", "run_server.py"]
