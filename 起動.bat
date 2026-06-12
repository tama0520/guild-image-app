@echo off
chcp 65001 >nul
cd /d C:\Users\23-3\Desktop\画像作成
rem 5秒後にブラウザを自動で開く（Streamlit起動待ち）
start "" /min cmd /c "timeout /t 5 >nul & start http://localhost:8501"
py -3.14 -m streamlit run streamlit_app.py
