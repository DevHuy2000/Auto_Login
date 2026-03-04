import os
worker_class = "gthread"
workers = 1
threads = 4
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
timeout = 120
