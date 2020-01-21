# tb-profiler-webserver

This repository hosts the code to deploy a webserver to wrap around the function of [TB-Profiler](https://github.com/jodyphelan/TBProfiler/). Updates will follow soon!

## Installation
Installation requires tb-profiler, flask, celery and rabbit-mq or redis.
To run it on your local machine:
```
# Install libraries
python setup.py install

# Run flask
export FLASK_APP=tbprofiler_web
export FLASK_ENV=development
flask run

# Run rabbit-mq server
rabbitmq-server

# Run celery
celery -A tbprofiler_web.worker worker --loglevel=info --concurrency=1
```
