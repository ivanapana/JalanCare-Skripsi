@echo off
cd /d "%~dp0"
echo JalanCare REVISI 2.8
echo Folder aktif: %CD%
echo Buka http://127.0.0.1:5000 setelah server berjalan.
if not exist .venv\Scripts\python.exe (
 echo Jalankan setup.bat dahulu.
 pause
 exit /b 1
)
.venv\Scripts\python.exe app.py
pause
