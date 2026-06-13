FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schedule_bot ./schedule_bot

USER appuser
EXPOSE 8080

CMD ["python", "-m", "schedule_bot"]

