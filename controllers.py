from flask import Blueprint, request, jsonify
from celery import Celery
from nmap_service import NmapService
from utils import is_valid_target, sanitize_input
from typing import Dict
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)

nmap_bp = Blueprint('nmap', __name__)
nmap_service = None
celery_app = None

# Rate limiting
RATE_LIMIT = 5  # requests
RATE_PERIOD = 60  # seconds
request_history = {}


def rate_limit(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        current_time = time.time()
        if ip in request_history:
            request_history[ip] = [
                t for t in request_history[ip]
                if current_time - t < RATE_PERIOD
            ]
            if len(request_history[ip]) >= RATE_LIMIT:
                return jsonify(
                    {"error":
                     "Rate limit exceeded. Please try again later."}), 429
        request_history.setdefault(ip, []).append(current_time)
        return f(*args, **kwargs)

    return decorated_function


def init_controllers(service: NmapService, celery: Celery):
    global nmap_service, celery_app
    nmap_service = service
    celery_app = celery

    # Define Celery task after celery_app is initialized
    @celery_app.task
    def run_nmap_scan(target: str, options: Dict[str, str]) -> Dict:
        if not is_valid_target(target):
            raise ValueError("Invalid IP address or hostname")
        result = nmap_service.run_scan(target, options)
        return nmap_service.result_parser.parse(result)

    # Update the scan function to use the newly defined task
    def scan():
        data = request.get_json()
        target = data.get('target')
        options = data.get('options', {})

        if not target:
            return jsonify({"error": "Target is required."}), 400

        target = sanitize_input(target)
        if not is_valid_target(target):
            return jsonify({"error": "Invalid IP address or hostname."}), 400

        try:
            task = run_nmap_scan.delay(target, options)
            logger.info(
                f"Scan initiated for target: {target}, task_id: {task.id}")
            return jsonify({"task_id": task.id}), 202
        except Exception as e:
            logger.error(f"Error initiating scan: {str(e)}", exc_info=True)
            return jsonify(
                {"error":
                 "Failed to initiate scan. Please try again later."}), 500

    # Register the updated scan function with the blueprint
    nmap_bp.route('/scan', methods=['POST'])(rate_limit(scan))


@nmap_bp.route('/scan/<task_id>', methods=['GET'])
def get_scan_result(task_id):
    try:
        task = celery_app.AsyncResult(task_id)
        if task.state == 'PENDING':
            response = {"status": "pending", "task_id": task_id}
        elif task.state == 'SUCCESS':
            response = {
                "status": "success",
                "result": task.result,
                "task_id": task_id
            }
        elif task.state == 'FAILURE':
            response = {
                "status": "failure",
                "error": str(task.result),
                "task_id": task_id
            }
        else:
            response = {"status": task.state, "task_id": task_id}
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error retrieving scan result: {str(e)}", exc_info=True)
        return jsonify({
            "error":
            "Failed to retrieve scan result. Please try again later."
        }), 500


@nmap_bp.route('/scans/<target>', methods=['GET'])
@rate_limit
def get_recent_scans(target):
    target = sanitize_input(target)
    if not is_valid_target(target):
        return jsonify({"error": "Invalid IP address or hostname."}), 400

    try:
        limit = int(request.args.get('limit', 5))
        scans = nmap_service.get_recent_scans(target, limit)
        return jsonify({"scans": scans})
    except Exception as e:
        logger.error(f"Error retrieving recent scans: {str(e)}", exc_info=True)
        return jsonify({
            "error":
            "Failed to retrieve recent scans. Please try again later."
        }), 500


@nmap_bp.route('/latest_scan/<target>', methods=['GET'])
@rate_limit
def get_latest_scan(target):
    target = sanitize_input(target)
    if not is_valid_target(target):
        return jsonify({"error": "Invalid IP address or hostname."}), 400

    try:
        scans = nmap_service.get_recent_scans(target, limit=1)
        if not scans:
            return jsonify({"error":
                            "No scans found for the given target."}), 404
        return jsonify({"latest_scan": scans[0]})
    except Exception as e:
        logger.error(f"Error retrieving latest scan: {str(e)}", exc_info=True)
        return jsonify({
            "error":
            "Failed to retrieve latest scan. Please try again later."
        }), 500


@nmap_bp.route('/scan_changes/<target>', methods=['GET'])
@rate_limit
def get_scan_changes(target):
    target = sanitize_input(target)
    if not is_valid_target(target):
        return jsonify({"error": "Invalid IP address or hostname."}), 400

    try:
        changes = nmap_service.get_scan_changes(target)
        return jsonify(changes)
    except Exception as e:
        logger.error(f"Error retrieving scan changes: {str(e)}", exc_info=True)
        return jsonify({
            "error":
            "Failed to retrieve scan changes. Please try again later."
        }), 500


@nmap_bp.route('/celery_status')
@rate_limit
def celery_status():
    try:
        i = celery_app.control.inspect()
        return jsonify({
            "active": i.active(),
            "scheduled": i.scheduled(),
            "reserved": i.reserved(),
        })
    except Exception as e:
        logger.error(f"Error retrieving Celery status: {str(e)}",
                     exc_info=True)
        return jsonify({
            "error":
            "Failed to retrieve Celery status. Please try again later."
        }), 500


@nmap_bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200


@nmap_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@nmap_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500
