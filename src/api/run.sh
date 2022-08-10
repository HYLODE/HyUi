#!/usr/bin/env sh

# python api/perrt/admission_probability/predictions_script.py &

# # Kill the above script on terminating run.sh
# trap 'pkill -P $$' SIGINT SIGTERM

uvicorn api.main:app --workers 1 --host 0.0.0.0 --port 8094
