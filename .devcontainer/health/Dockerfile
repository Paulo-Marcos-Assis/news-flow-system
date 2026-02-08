# Use a slim and official Python runtime as a parent image
FROM python:3.9-slim
WORKDIR /app

COPY .devcontainer/health/requirements.txt .
COPY .devcontainer/health/stack-health.py .

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x stack-health.py

HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 CMD python3 ./stack-health.py

CMD ["python3" ,"./stack-health.py" ,"&&" ,"tail", "-f", "/dev/null"]
