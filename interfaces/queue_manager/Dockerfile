FROM python:3.9-slim

WORKDIR /app

# Install Docker CLI for container management
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://get.docker.com -o get-docker.sh \
    && sh get-docker.sh \
    && rm get-docker.sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api.py .
COPY index.html .

# Expose port
EXPOSE 5555

# Run the API server
CMD ["python", "-u", "api.py"]
