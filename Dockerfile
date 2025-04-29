FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установка postgresql-client для pg_dump
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /task_flow

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем директорию для бэкапов
RUN mkdir -p /backups && chmod 777 /backups

CMD ["sh", "-c", "cd /task_flow && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]