echo off
echo building python project...
echo.


mkdir "../build"
mkdir "../build/dist"
mkdir "../build/build"

start /b ../.venv/Scripts/pyinstaller.exe -c -i ../icon.ico --distpath ../build/dist --workpath ../build/build --specpath ../build ../main.py


echo.
echo Done!
pause
exit