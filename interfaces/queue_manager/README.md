# CEOS Data Ingestion System Manager

A web interface for managing RabbitMQ queues and Docker containers in the CEOS data ingestion system.

## Features

- **Queue Management**
  - View all queues and message counts
  - Preview messages in queues (without consuming)
  - Move messages between queues
  - Purge queues

- **Container Management**
  - View all Docker containers and their status
  - View container logs
  - Restart containers
  - View resource stats (CPU, Memory)

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API server

```bash
python api.py
```

The API will run on `http://localhost:5555`

### 3. Open the interface

Open `index.html` in your browser, or serve it:

```bash
python -m http.server 8080
```

Then navigate to `http://localhost:8080`

## API Endpoints

### Queues

- `GET /api/queues` - List all queues with message counts
- `GET /api/queues/<name>/messages?limit=10` - Preview messages
- `POST /api/queues/<name>/purge` - Purge all messages
- `POST /api/queues/move` - Move messages between queues
- `POST /api/queues/<name>/requeue` - Move specific message

### Containers

- `GET /api/containers` - List all containers
- `GET /api/containers/<name>/logs?lines=100` - Get container logs
- `POST /api/containers/<name>/restart` - Restart container
- `GET /api/containers/<name>/stats` - Get resource stats

## Configuration

Edit `api.py` to change RabbitMQ connection settings:

```python
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_VHOST = '/'
RABBITMQ_USER = 'admin'
RABBITMQ_PASSWORD = 'admin'
```
