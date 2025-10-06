@echo off
echo ========================================
echo  Iniciando Servidor de Clustering
echo ========================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat
python clustering_server.py

pause
