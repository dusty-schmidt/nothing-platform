#!/bin/bash
# GOB Dashboard startup
cd "$(dirname "$0")"
export FLASK_APP=app.py
nohup python3 app.py >> /tmp/gob-dashboard.log 2>&1 &
echo "GOB Dashboard started — PID $!"
echo "Access at http://localhost:7842"
