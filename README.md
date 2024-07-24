# Nmap Web Service

A web service for running Nmap scans, retrieving results, and comparing changes between scans.

## Prerequisites

- Python 3.8+
- Nmap
- Flask
- Celery

## Installing Nmap (RPM-based Linux)

For RPM-based Linux distributions (like Red Hat, CentOS, Fedora), use these commands:

```bash
sudo rpm -vhU https://nmap.org/dist/nmap-7.95-2.x86_64.rpm
sudo rpm -vhU https://nmap.org/dist/ncat-7.95-2.x86_64.rpm
sudo rpm -vhU https://nmap.org/dist/nping-0.7.95-2.x86_64.rpm
```

Verify the installation:
```bash
nmap --version
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nmap-web-service.git
   cd nmap-web-service
   ```

2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python main.py
```

## API Endpoints

- `POST /scan`: Initiate a new Nmap scan
- `GET /scan/<task_id>`: Retrieve the result of a specific scan
- `GET /scans/<target>`: Get recent scans for a specific target
- `GET /latest_scan/<target>`: Get the most recent scan for a target
- `GET /scan_changes/<target>`: Get changes between the two most recent scans for a target
- `GET /celery_status`: Get the status of Celery tasks
- `GET /health`: Health check endpoint

## Assumptions

1. Nmap is installed and available in the system PATH.
2. The application is run in a controlled environment where it's safe to execute Nmap scans.
3. Only the two most recent scans are compared for changes.
4. All Nmap options provided by the user are considered valid and safe to use.
5. The application is not using Docker for containerization.
6. IP addresses and hostnames are not interchangeable in comparisons (i.e., we only compare IP to IP or hostname to hostname).
7. The Celery worker runs in the same process as the Flask application.
8. SQLite is sufficient for the database backend (not suitable for high concurrency).
