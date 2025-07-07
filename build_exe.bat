@echo off
chcp 65001
echo vMix Tally System packaging started...

echo 1. Installing required packages...
pip install pyinstaller websockets requests PyQt5

echo 2. Creating EXE file with PyInstaller...
pyinstaller --clean build_tally.spec

echo 3. Build complete! vMix_Tally_System.exe file has been created in the dist folder.
echo Executable file path: %cd%\dist\vMix_Tally_System.exe

pause