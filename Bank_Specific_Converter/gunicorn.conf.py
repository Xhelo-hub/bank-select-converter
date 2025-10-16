# Gunicorn Configuration for Bank Statement Converter
# =================================================

import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/gunicorn/bank_converter_access.log"
errorlog = "/var/log/gunicorn/bank_converter_error.log"
loglevel = "info"

# Process naming
proc_name = 'bank_statement_converter'

# Server mechanics
preload_app = True
daemon = False
pidfile = "/var/run/gunicorn/bank_converter.pid"
user = "admin"  # Change to your HestiaCP user
group = "admin"  # Change to your HestiaCP group
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/ssl/key"
# certfile = "/path/to/ssl/cert"