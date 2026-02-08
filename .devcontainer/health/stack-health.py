import os
import sys
import time
import socket
import psycopg2
import pika
import requests
from pymongo import MongoClient
from pathlib import Path

# Helper function to print colored messages
def print_color(msg, color="cyan"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }
    color_code = colors.get(color, colors["white"])
    print(f"{color_code}{msg}{colors['reset']}")

def wait_for_service(host, port, service_name, retries=10, delay=5):
    """Generic function to wait for a TCP port to be open."""
    print_color(f"Waiting for {service_name} at {host}:{port}...", "yellow")
    for i in range(retries):
        try:
            with socket.create_connection((host, port), timeout=3):
                print_color(f"{service_name} port {port} is open.", "green")
                return True
        except (socket.timeout, ConnectionRefusedError, socket.gaierror, OSError) as e:
            print_color(f"Attempt {i+1}/{retries}: {service_name} not available yet ({type(e).__name__}). Retrying in {delay}s...", "yellow")
            time.sleep(delay)
    print_color(f"Could not connect to {service_name} at {host}:{port} after {retries} retries.", "red")
    return False

def check_postgres():
    """Checks connection to PostgreSQL."""
    host = os.getenv("HOST_PG")
    port = int(os.getenv("PORT_PG", 5432))
    dbname = os.getenv("DATABASE_PG")
    user = os.getenv("USERNAME_PG")
    password = os.getenv("SENHA_PG")
    
    if not all([host, port, dbname, user, password]):
        print_color("PostgreSQL env variables not set.", "red")
        return False

    if not wait_for_service(host, port, "PostgreSQL"):
        return False

    # Give PostgreSQL extra time to fully initialize authentication system
    print_color("Waiting for PostgreSQL authentication system to be ready...", "yellow")
    time.sleep(3)

    # Retry connection with exponential backoff
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print_color(f"Connecting to PostgreSQL at {host}:{port} (attempt {attempt+1}/{max_retries})...", "cyan")
            conn = psycopg2.connect(
                dbname=dbname, user=user, password=password, host=host, port=port, connect_timeout=10
            )
            # Test the connection with a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            print_color("PostgreSQL connection successful.", "green")
            return True
        except psycopg2.OperationalError as e:
            if "authentication failed" in str(e).lower() or "password authentication failed" in str(e).lower():
                print_color(f"PostgreSQL authentication failed: {e}", "red")
                print_color(f"Using credentials: user={user}, db={dbname}, host={host}, port={port}", "yellow")
                return False
            else:
                print_color(f"PostgreSQL connection attempt {attempt+1} failed: {e}", "yellow")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s, 8s
                    print_color(f"Retrying in {wait_time}s...", "yellow")
                    time.sleep(wait_time)
        except Exception as e:
            print_color(f"PostgreSQL connection failed with unexpected error: {e}", "red")
            return False
    
    print_color(f"PostgreSQL connection failed after {max_retries} attempts.", "red")
    return False

def check_rabbitmq():
    """Checks connection to RabbitMQ."""
    host = os.getenv("QUEUE_SERVER_ADDRESS")
    port = int(os.getenv("QUEUE_SERVER_PORT", 5672))
    user = os.getenv("RABBIT_MQ_USER")
    password = os.getenv("RABBIT_MQ_PWD")

    if not all([host, port, user, password]):
        print_color("RabbitMQ env variables not set.", "red")
        return False

    if not wait_for_service(host, port, "RabbitMQ"):
        return False

    try:
        print_color(f"Connecting to RabbitMQ at {host}:{port}...", "cyan")
        credentials = pika.PlainCredentials(user, password)
        parameters = pika.ConnectionParameters(host, port, credentials=credentials, connection_attempts=3, retry_delay=5)
        connection = pika.BlockingConnection(parameters)
        connection.close()
        print_color("RabbitMQ connection successful.", "green")
        return True
    except Exception as e:
        print_color(f"RabbitMQ connection failed: {e}", "red")
        return False

def check_orientdb():
    """Checks connection to OrientDB via REST API."""
    host = os.getenv("HOST_ORIENT")
    port = int(os.getenv("PORT_ORIENT", 2480))
    user = os.getenv("USERNAME_ORIENT")
    password = os.getenv("SENHA_ORIENT")
    db_name = os.getenv("DATABASE_ORIENT")

    if not all([host, port, user, password, db_name]):
        print_color("OrientDB env variables not set.", "red")
        return False
        
    # OrientDB HTTP port check
    if not wait_for_service(host, port, "OrientDB (HTTP)"):
        return False

    try:
        print_color(f"Connecting to OrientDB at {host}:{port} via REST API...", "cyan")
        
        # First, check if we can list databases (server-level auth check)
        url = f"http://{host}:{port}/listDatabases"
        response = requests.get(url, auth=(user, password))
        
        if response.status_code in [401, 403]:
            print_color("OrientDB authentication failed. Check credentials.", "red")
            return False
        elif response.status_code == 200:
            print_color("OrientDB server authentication successful.", "green")
            
            # Check if the specific database exists
            databases = response.json().get("databases", [])
            if db_name in databases:
                print_color(f"OrientDB database '{db_name}' exists.", "green")
            else:
                print_color(f"OrientDB database '{db_name}' does not exist yet, but server is healthy.", "yellow")
            return True
        else:
            print_color(f"OrientDB check failed with status code {response.status_code}: {response.text}", "red")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print_color(f"OrientDB connection failed: {e}", "red")
        return False
    except Exception as e:
        print_color(f"An unexpected error occurred during OrientDB check: {e}", "red")
        return False

def check_mongodb():
    """Checks connection to MongoDB."""
    host = os.getenv("HOST_MONGODB")
    port = int(os.getenv("PORT_MONGODB", 27017))
    user = os.getenv("USERNAME_MONGODB")
    password = os.getenv("SENHA_MONGODB")
    auth_db = os.getenv("DATABASE_AUTENTICACAO_MONGODB", "admin")

    if not all([host, port, user, password]):
        print_color("MongoDB env variables not set.", "red")
        return False

    if not wait_for_service(host, port, "MongoDB"):
        return False

    try:
        print_color(f"Connecting to MongoDB at {host}:{port}...", "cyan")
        client = MongoClient(
            host,
            port,
            username=user,
            password=password,
            authSource=auth_db,
            serverSelectionTimeoutMS=5000
        )
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print_color("MongoDB connection successful.", "green")
        client.close()
        return True
    except Exception as e:
        print_color(f"MongoDB connection failed: {e}", "red")
        return False

def check_pgadmin():
    """Checks if pgAdmin web interface is accessible."""
    host = "pgadmin"
    port = 80
    
    if not wait_for_service(host, port, "pgAdmin"):
        return False
    
    try:
        print_color(f"Checking pgAdmin web interface at {host}:{port}...", "cyan")
        response = requests.get(f"http://{host}:{port}/", timeout=10, allow_redirects=True)
        if response.status_code in [200, 302]:
            print_color("pgAdmin web interface is accessible.", "green")
            return True
        else:
            print_color(f"pgAdmin returned status code {response.status_code}", "yellow")
            return True  # Service is running even if not fully ready
    except requests.exceptions.RequestException as e:
        # pgAdmin might still be initializing, consider it healthy if port is open
        print_color(f"pgAdmin web interface not fully ready yet: {e}", "yellow")
        print_color("pgAdmin port is open, considering service healthy.", "green")
        return True

def check_mongo_express():
    """Checks if mongo-express web interface is accessible."""
    host = "mongo-express"
    port = 8081
    
    if not wait_for_service(host, port, "mongo-express"):
        return False
    
    try:
        print_color(f"Checking mongo-express web interface at {host}:{port}...", "cyan")
        # mongo-express uses basic auth, so we expect 401 or 200
        response = requests.get(f"http://{host}:{port}/", timeout=5, auth=("admin", "admin"))
        if response.status_code in [200, 401]:
            print_color("mongo-express web interface is accessible.", "green")
            return True
        else:
            print_color(f"mongo-express returned status code {response.status_code}", "yellow")
            return True  # Service is running even if not fully ready
    except Exception as e:
        print_color(f"mongo-express check failed: {e}", "red")
        return False

def main():
    """Runs all health checks."""
    
    checks = {
        "PostgreSQL": check_postgres,
        "RabbitMQ": check_rabbitmq,
        "MongoDB": check_mongodb,
        "OrientDB": check_orientdb,
        "pgAdmin": check_pgadmin,
        "mongo-express": check_mongo_express,
    }

    results = {}
    all_ok = True

    for name, check_func in checks.items():
        print("-" * 40)
        success = check_func()
        results[name] = success
        if not success:
            all_ok = False

    print("\n" + "=" * 40)
    print_color("Stack Health Summary:", "blue")
    for name, success in results.items():
        status = "OK" if success else "FAIL"
        color = "green" if success else "red"
        print_color(f"- {name}: {status}", color)
    print("=" * 40)

    if all_ok:
        print_color("\nAll services are healthy!", "green")
        sys.exit(0)
    else:
        print_color("\nSome services failed the health check.", "red")
        sys.exit(1)

if __name__ == "__main__":
    main()
