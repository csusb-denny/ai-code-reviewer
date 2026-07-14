FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port for webhook
EXPOSE 8080

ENV PYTHONUNBUFFERED=1

# Default command: run webhook
CMD ["uvicorn", "app.webhook:app", "--host", "0.0.0.0", "--port", "8080"]