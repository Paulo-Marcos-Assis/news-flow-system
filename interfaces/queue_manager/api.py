#!/usr/bin/env python3
"""Queue Manager API - Backend for managing RabbitMQ queues and Docker containers."""

import json
import os
import subprocess
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pika

app = Flask(__name__, static_folder='.')
CORS(app)

# RabbitMQ configuration (use environment variables or defaults)
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_VHOST = os.environ.get('RABBITMQ_VHOST', '/')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'admin')
RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'admin')

# Docker/Container configuration
RABBITMQ_CONTAINER_NAME = os.environ.get('RABBITMQ_CONTAINER_NAME', 'main-server-rabbitmq-1')
DOCKER_COMPOSE_FILE = os.environ.get('DOCKER_COMPOSE_FILE', '/project/docker-compose.yml')
PROJECT_NAME = os.environ.get('PROJECT_NAME', 'main-server')
CONTAINER_NAME_PREFIX = os.environ.get('CONTAINER_NAME_PREFIX', 'main-server-')


@app.route('/')
def serve_index():
    """Serve the main HTML interface."""
    return send_from_directory('.', 'index.html')


def get_rabbitmq_connection():
    """Create a RabbitMQ connection."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)


@app.route('/api/queues', methods=['GET'])
def list_queues():
    """List all queues with their message counts (ready, unacked, total)."""
    try:
        # Use rabbitmqctl to list queues with detailed message counts
        result = subprocess.run(
            ['docker', 'exec', RABBITMQ_CONTAINER_NAME, 
             'rabbitmqctl', 'list_queues', 'name', 'messages', 'messages_ready', 
             'messages_unacknowledged', 'consumers', '--formatter=json'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            queues_data = json.loads(result.stdout)
            queues = []
            for q in queues_data:
                queues.append({
                    'name': q.get('name', ''),
                    'messages': q.get('messages', 0),
                    'ready': q.get('messages_ready', 0),
                    'unacked': q.get('messages_unacknowledged', 0),
                    'consumers': q.get('consumers', 0)
                })
            return jsonify({'success': True, 'queues': queues})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/queues/<queue_name>/messages', methods=['GET'])
def get_queue_messages(queue_name):
    """Get messages from a queue (peek without consuming)."""
    try:
        limit = int(request.args.get('limit', 10))
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Collect all messages first, then nack them all at once
        collected = []
        seen_tags = set()
        
        for _ in range(limit * 2):  # Try more times to handle redelivery
            method, properties, body = channel.basic_get(queue=queue_name, auto_ack=False)
            if method is None:
                break
            
            # Skip if we've already seen this delivery tag
            if method.delivery_tag in seen_tags:
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                continue
                
            seen_tags.add(method.delivery_tag)
            
            try:
                msg_body = json.loads(body.decode('utf-8'))
            except:
                msg_body = body.decode('utf-8', errors='replace')
            
            collected.append({
                'delivery_tag': method.delivery_tag,
                'redelivered': method.redelivered,
                'body': msg_body
            })
            
            if len(collected) >= limit:
                break
        
        # Nack all collected messages to put them back
        for msg in collected:
            try:
                channel.basic_nack(delivery_tag=msg['delivery_tag'], requeue=True)
            except:
                pass
        
        connection.close()
        return jsonify({'success': True, 'messages': collected, 'count': len(collected)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/queues/<queue_name>/purge', methods=['POST'])
def purge_queue(queue_name):
    """Purge all messages from a queue."""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_purge(queue=queue_name)
        connection.close()
        return jsonify({'success': True, 'message': f'Purged queue {queue_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/queues/<queue_name>/publish', methods=['POST'])
def publish_message(queue_name):
    """Publish a message to a queue."""
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'success': False, 'error': 'message is required'}), 400
        
        # If message is a string, try to parse as JSON, otherwise use as-is
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                pass  # Keep as string
        
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Ensure queue exists
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Publish message
        body = json.dumps(message) if isinstance(message, (dict, list)) else str(message)
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=body,
            properties=pika.BasicProperties(delivery_mode=2)  # Persistent
        )
        
        connection.close()
        return jsonify({'success': True, 'message': f'Published message to {queue_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/queues/move', methods=['POST'])
def move_messages():
    """Move messages from one queue to another. If message has original_message, only send that."""
    try:
        data = request.get_json()
        source_queue = data.get('source')
        target_queue = data.get('target')
        count = int(data.get('count', 1))
        
        if not source_queue or not target_queue:
            return jsonify({'success': False, 'error': 'source and target queues required'}), 400
        
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Ensure target queue exists
        channel.queue_declare(queue=target_queue, durable=True)
        
        moved = 0
        for _ in range(count):
            method, properties, body = channel.basic_get(queue=source_queue, auto_ack=False)
            if method is None:
                break
            
            # Try to extract original_message if present
            body_to_send = body
            try:
                msg_data = json.loads(body.decode('utf-8'))
                if isinstance(msg_data, dict) and 'original_message' in msg_data:
                    original = msg_data['original_message']
                    # original_message might be a string (JSON) or already parsed
                    if isinstance(original, str):
                        body_to_send = original.encode('utf-8')
                    else:
                        body_to_send = json.dumps(original).encode('utf-8')
            except:
                pass  # Keep original body if parsing fails
            
            # Publish to target queue
            channel.basic_publish(
                exchange='',
                routing_key=target_queue,
                body=body_to_send,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            # Acknowledge from source
            channel.basic_ack(delivery_tag=method.delivery_tag)
            moved += 1
        
        connection.close()
        return jsonify({'success': True, 'moved': moved, 'source': source_queue, 'target': target_queue})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/queues/<queue_name>/requeue', methods=['POST'])
def requeue_message(queue_name):
    """Move a specific message to another queue, optionally with edited content."""
    try:
        data = request.get_json()
        target_queue = data.get('target')
        message_index = int(data.get('index', 0))
        edited_body = data.get('edited_body')  # Optional: edited message content
        
        if not target_queue:
            return jsonify({'success': False, 'error': 'target queue required'}), 400
        
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Ensure target queue exists
        channel.queue_declare(queue=target_queue, durable=True)
        
        # Get messages until we reach the target index
        for i in range(message_index + 1):
            method, properties, body = channel.basic_get(queue=queue_name, auto_ack=False)
            if method is None:
                connection.close()
                return jsonify({'success': False, 'error': 'Message not found'}), 404
            
            if i < message_index:
                # Not the target message, put back
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                # Target message, move to new queue
                # Use edited body if provided, otherwise use original
                if edited_body is not None:
                    if isinstance(edited_body, str):
                        try:
                            # Try to parse as JSON to validate
                            json.loads(edited_body)
                            body_to_send = edited_body.encode('utf-8')
                        except json.JSONDecodeError:
                            body_to_send = edited_body.encode('utf-8')
                    else:
                        body_to_send = json.dumps(edited_body).encode('utf-8')
                else:
                    body_to_send = body
                
                channel.basic_publish(
                    exchange='',
                    routing_key=target_queue,
                    body=body_to_send,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                channel.basic_ack(delivery_tag=method.delivery_tag)
        
        connection.close()
        return jsonify({'success': True, 'message': f'Moved message to {target_queue}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers', methods=['GET'])
def list_containers():
    """List all Docker containers with their status (main-server project only)."""
    try:
        # Filter to only show project containers
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', f'name={CONTAINER_NAME_PREFIX}', '--format', 
             '{"name":"{{.Names}}","status":"{{.Status}}","image":"{{.Image}}","ports":"{{.Ports}}","state":"{{.State}}"}'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))
            return jsonify({'success': True, 'containers': containers})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers/<container_name>/logs', methods=['GET'])
def get_container_logs(container_name):
    """Get logs from a Docker container."""
    try:
        lines = int(request.args.get('lines', 100))
        result = subprocess.run(
            ['docker', 'logs', '--tail', str(lines), container_name],
            capture_output=True, text=True, timeout=30
        )
        
        # Docker logs go to stderr for some containers
        logs = result.stdout or result.stderr
        return jsonify({'success': True, 'logs': logs, 'container': container_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers/<container_name>/start', methods=['POST'])
def start_container(container_name):
    """Start a Docker container."""
    try:
        result = subprocess.run(
            ['docker', 'start', container_name],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Started {container_name}'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers/<container_name>/stop', methods=['POST'])
def stop_container(container_name):
    """Stop a Docker container."""
    try:
        result = subprocess.run(
            ['docker', 'stop', container_name],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Stopped {container_name}'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers/<container_name>/restart', methods=['POST'])
def restart_container(container_name):
    """Restart a Docker container."""
    try:
        result = subprocess.run(
            ['docker', 'restart', container_name],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Restarted {container_name}'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers/<container_name>/rebuild', methods=['POST'])
def rebuild_container(container_name):
    """Rebuild a Docker container image using docker compose."""
    try:
        # Extract service name from container name (e.g., main-server-collector-esfinge-1 -> collector-esfinge)
        service_name = container_name.replace(CONTAINER_NAME_PREFIX, '').rsplit('-', 1)[0]
        
        # Use 'docker compose' with project name to avoid duplicates
        compose_cmd = ['docker', 'compose', '-f', DOCKER_COMPOSE_FILE, '-p', PROJECT_NAME]
        
        # Build the image
        build_result = subprocess.run(
            compose_cmd + ['build', '--no-cache', service_name],
            capture_output=True, text=True, timeout=300
        )
        
        if build_result.returncode != 0:
            return jsonify({'success': False, 'error': f'Build failed: {build_result.stderr}'}), 500
        
        # Restart the container with new image
        up_result = subprocess.run(
            compose_cmd + ['up', '-d', '--force-recreate', service_name],
            capture_output=True, text=True, timeout=60
        )
        
        if up_result.returncode == 0:
            return jsonify({'success': True, 'message': f'Rebuilt and restarted {service_name}'})
        else:
            return jsonify({'success': False, 'error': f'Restart failed: {up_result.stderr}'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Build timed out (5 min limit)'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers/restart-all', methods=['POST'])
def restart_all_containers():
    """Restart all running containers using docker compose."""
    try:
        compose_cmd = ['docker', 'compose', '-f', DOCKER_COMPOSE_FILE, '-p', PROJECT_NAME]
        result = subprocess.run(
            compose_cmd + ['restart'],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'All containers restarted'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Restart timed out'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers/rebuild-all', methods=['POST'])
def rebuild_all_containers():
    """Rebuild all containers using docker compose."""
    try:
        compose_cmd = ['docker', 'compose', '-f', DOCKER_COMPOSE_FILE, '-p', PROJECT_NAME]
        
        # Build all images
        build_result = subprocess.run(
            compose_cmd + ['build', '--no-cache'],
            capture_output=True, text=True, timeout=600
        )
        
        if build_result.returncode != 0:
            return jsonify({'success': False, 'error': f'Build failed: {build_result.stderr}'}), 500
        
        # Restart with new images
        up_result = subprocess.run(
            compose_cmd + ['up', '-d', '--force-recreate'],
            capture_output=True, text=True, timeout=120
        )
        
        if up_result.returncode == 0:
            return jsonify({'success': True, 'message': 'All containers rebuilt and restarted'})
        else:
            return jsonify({'success': False, 'error': f'Restart failed: {up_result.stderr}'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Build timed out (10 min limit)'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/containers/<container_name>/stats', methods=['GET'])
def get_container_stats(container_name):
    """Get resource stats for a container."""
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format',
             '{"cpu":"{{.CPUPerc}}","memory":"{{.MemUsage}}","memPercent":"{{.MemPerc}}","netIO":"{{.NetIO}}"}',
             container_name],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            stats = json.loads(result.stdout.strip())
            return jsonify({'success': True, 'stats': stats, 'container': container_name})
        else:
            return jsonify({'success': False, 'error': result.stderr or 'No stats available'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
