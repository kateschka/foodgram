FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:9000", "backend.wsgi"]
