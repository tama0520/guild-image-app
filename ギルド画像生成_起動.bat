@echo off
cd /d "%~dp0"
echo ギルド画像生成アプリを起動しています...
py -3.14 -m streamlit run streamlit_app.py
pause
