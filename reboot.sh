#!/bin/bash
pkill -f gunicorn
nohup gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:8000 app:app &
