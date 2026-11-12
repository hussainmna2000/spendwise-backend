"""Render-compatible defaults for a plain ``gunicorn app:app`` start command."""

import os


bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = 4
timeout = 120
accesslog = "-"
