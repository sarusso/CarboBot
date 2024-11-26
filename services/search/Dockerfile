FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

COPY ./src /app

#CMD ["fastapi", "run", "/app/main.py", "--port", "80"]
CMD ["fastapi", "dev", "/app/main.py", "--port", "80", "--host", "0.0.0.0"]