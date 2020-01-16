rabbitmq-server &
celery -A tbprofiler_web.worker worker --loglevel=info --concurrency=1

