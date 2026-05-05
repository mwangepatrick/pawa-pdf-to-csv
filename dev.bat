@echo off
start "DataDrop Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "DataDrop Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
