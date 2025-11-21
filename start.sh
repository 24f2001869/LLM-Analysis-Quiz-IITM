#!/bin/bash
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --host 0.0.0.0 --port $PORT
