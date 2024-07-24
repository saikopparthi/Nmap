import os
import logging
import threading
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

# Initialize Flask app
app = Flask(__name__)

# Celery configuration
sqlite_db_path = os.path.abspath('celery.sqlite')
app.config['CELERY_BROKER_URL'] = f'sqla+sqlite:///{sqlite_db_path}'
app.config['CELERY_RESULT_BACKEND'] = f'db+sqlite:///{sqlite_db_path}'
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
  worker = celery.Worker(concurrency=1, loglevel='info')
  worker.start()


if __name__ == '__main__':
  # Start Celery worker in a separate thread
  celery_thread = threading.Thread(target=run_celery_worker)
  celery_thread.start()
  app.run(debug=True)
