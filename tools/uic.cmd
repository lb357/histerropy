echo off
echo uic .ui files...
echo.


start /b ../.venv/Lib/site-packages/PySide6/uic.exe ../ui/mainwindow.ui -g python -o ../ui_mainwindow.py
start /b ../.venv/Lib/site-packages/PySide6/uic.exe ../ui/info.ui -g python -o ../ui_info.py


echo.
echo Done!
pause
exit