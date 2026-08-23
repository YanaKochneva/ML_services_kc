FROM python:3.12-slim

WORKDIR /app

# Контекст сборки — это каталог ml_worker/
COPY requirements.txt /app/
COPY main.py /app/ml_worker/main.py

RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# В контейнере код приложения монтируется в /app/app (модели, database, services),
# поэтому добавляем /app/app в PYTHONPATH, чтобы работали импорты:
#   from database.database import engine
#   from models.ml_task import MLTask
#   from services.qwen_service import QwenService
ENV PYTHONPATH=/app/app:/app

# Важно: main.py находится в ml_worker/ внутри образа
CMD ["python", "/app/ml_worker/main.py"]
