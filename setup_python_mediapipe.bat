@echo off
echo Installing Python MediaPipe dependencies...
cd backend
pip install -r requirements.txt
echo.
echo Python MediaPipe setup complete!
echo.
echo To start the backend with Python MediaPipe:
echo python run.py
echo.
echo To start the frontend:
echo cd ..\frontend
echo npm run dev
echo.
pause
