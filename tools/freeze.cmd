echo off
echo freezing python dependencies...
echo.


start /b ../.venv/Scripts/pip.exe freeze > ../requirements.txt


echo.
echo Done!
pause
exit