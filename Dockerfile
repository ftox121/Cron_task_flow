FROM python:3.12

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

WORKDIR /app/task_flow

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]