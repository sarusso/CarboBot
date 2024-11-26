FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# Install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

# Copy code
COPY ./code /code

# Set work dir (this is the dir that will be watched for changes)
WORKDIR /code

# Run command
CMD ["fastapi", "dev", "/code/main.py", "--port", "80", "--host", "0.0.0.0"]