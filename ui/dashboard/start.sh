#!/bin/bash
# GOB Dashboard startup
cd "$(dirname "$0")"
export FLASK_APP=app.py

# Regenerate auth token cache
/opt/venv-a0/bin/python3 -c "
import sys; sys.path.insert(0, '/a0')
from python.helpers.settings import create_auth_token
open('/a0/usr/.gob_token','w').write(create_auth_token())
" 2>/dev/null && echo "Token cached" || echo "Token cache failed (non-fatal)"

nohup /opt/venv/bin/python3 app.py >> /tmp/gob-dashboard.log 2>&1 &
echo "GOB Dashboard started — PID $!"
echo "Access at http://localhost:7842"
