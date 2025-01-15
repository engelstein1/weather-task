FROM python:3.9-slim

LABEL maintainer="Weather Service"
LABEL description="Weather Data Service for Azure Interview Task"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY api.py .
COPY weather_analytics.py .
COPY database ./database

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]