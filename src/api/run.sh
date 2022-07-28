#!/usr/bin/env sh

python api/perrt/admission_probability/predictions_script.py &
uvicorn api.main:app --workers 1 --host 0.0.0.0 --port 8094