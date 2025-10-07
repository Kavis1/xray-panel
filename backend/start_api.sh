#!/bin/bash
# Wrapper script to start API with correct environment

cd /root/panel/backend

# Unset conflicting env vars and load from .env
unset XRAY_SUBSCRIPTION_URL_PREFIX

# Start API
exec venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
