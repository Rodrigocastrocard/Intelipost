@echo off
title Templarios API
color 0A

cd /
cd "C:\Users\Computador\PycharmProjects\PythonProject\.venv\Templariosapp"
call .venv\Scripts\activate
pip install flask mysql-connector-python --quiet
python app.py
pause
