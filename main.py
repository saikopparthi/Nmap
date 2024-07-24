import os
import logging
import threading
import subprocess
import atexit
import time
import redis
from flask import Flask
from celery import Celery
from database import SQLiteDatabase
from nmap_scanner import NmapScanner
from nmap_parser import NmapResultParser
from nmap_service import NmapService
from controllers import nmap_bp, init_controllers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to check if Redis is running
def is_redis_running():
    try:
        client = redis.StrictRedis(host='localhost', port=6379)
        client.ping()
        return True
    except redis.ConnectionError:
        return False

# Start Redis server if not running
redis_process = None
if not is_redis_running():
    redis_process = subprocess.Popen(['redis-server'],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)

    # Wait for Redis to start
    time.sleep(2)  # Give Redis a moment to start up

    # Check if Redis started successfully
    if redis_process.poll() is not None:
        logger.error("Failed to start Redis server")
        exit(1)

    logger.info("Redis server started")
else:
    logger.info("Redis server is already running")

# Function to stop Redis server
def stop_redis():
    if redis_process:
        logger.info("Stopping Redis server")
        redis_process.terminate()
        redis_process.wait()

# Register the function to be called on exit
atexit.register(stop_redis)

# Initialize Flask app
app = Flask(__name__)

# Celery configuration with Redis
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Initialize services
db_manager = SQLiteDatabase('nmap_scans.db')
db_manager.init_db()
nmap_scanner = NmapScanner()
result_parser = NmapResultParser()
nmap_service = NmapService(nmap_scanner, result_parser, db_manager)

# Initialize controllers with dependencies
init_controllers(nmap_service, celery)

# Register blueprint
app.register_blueprint(nmap_bp)

def run_celery_worker():
    while True:
        try:
            worker = celery.Worker(concurrency=1, loglevel='info')
            worker.start()
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Error connecting to Redis: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == '__main__':
    # Start Celery worker in a separate thread
    celery_thread = threading.Thread(target=run_celery_worker)
    celery_thread.start()

    # Ensure Flask app retries connection to Redis
    for _ in range(5):
        try:
            app.run(debug=True)
            break
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Error connecting to Redis: {e}")
            time.sleep(5)  # Wait before retrying
