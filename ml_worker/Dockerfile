FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/
COPY main.py /app/ml_worker/main.py

RUN pip install --upgrade pip && pip install -r /app/requirements.txt

ENV PYTHONPATH=/app/app:/app

CMD ["python", "/app/ml_worker/main.py"]
