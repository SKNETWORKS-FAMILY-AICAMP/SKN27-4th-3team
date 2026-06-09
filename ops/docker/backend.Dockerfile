FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend backend
COPY api-spec api-spec

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]
