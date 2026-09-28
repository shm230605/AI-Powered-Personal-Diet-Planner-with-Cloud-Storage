FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8080

WORKDIR /app
COPY backend/requirements-cloud.txt backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements-cloud.txt
COPY backend/app ./backend/app
WORKDIR /app/backend

EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
