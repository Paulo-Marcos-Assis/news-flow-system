
FROM python:3.9-slim
WORKDIR /app
COPY ./service_essentials/ ./service_essentials/
COPY ./data_dependencies/ ./data_dependencies/
RUN pip install -r service_essentials/requirements.txt
CMD ["python", "-u", "main.py"]