bind = '127.0.0.1:5002'
workers = 4
timeout = 300
accesslog = 'app_access.log'
errorlog = 'app_error.log'
# daemon = True  # Commented out for systemd compatibility
pidfile = 'gunicorn.pid'
