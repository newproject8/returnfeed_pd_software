@echo off
echo === DIAGNOSTIC TOOL ===
echo.

echo 1. Checking current directory...
echo Current: %CD%
echo Script: %~dp0
echo.

echo 2. Listing Python installations...
where python
echo.

echo 3. Python default version...
python --version 2>&1
echo.

echo 4. Checking file encoding...
powershell -Command "Get-Content run.bat -First 1 | Format-Hex"
echo.

echo 5. Testing simple Python execution...
python -c "print('Python works!')" 2>&1
echo Exit code: %ERRORLEVEL%
echo.

echo 6. Testing PyQt6...
python -c "import PyQt6; print('PyQt6 OK')" 2>&1
echo Exit code: %ERRORLEVEL%
echo.

echo 7. Checking for BOM in run.bat...
powershell -Command "$bytes = [System.IO.File]::ReadAllBytes('run.bat'); if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { 'BOM FOUND!' } else { 'No BOM' }"
echo.

echo 8. Creating clean run.bat...
echo @echo off > run_clean.bat
echo cd /d "%%~dp0" >> run_clean.bat
echo python main.py >> run_clean.bat
echo pause >> run_clean.bat
echo Created run_clean.bat
echo.

pause