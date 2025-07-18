# PowerShell script to fix batch file encoding
$files = @("run.bat", "install_ffmpeg.bat", "install_ffmpeg_portable.bat")

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Fixing encoding for $file..." -ForegroundColor Yellow
        
        # Read with current encoding
        $content = Get-Content $file -Raw
        
        # Write with UTF-8 without BOM
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText("$pwd\$file", $content, $utf8NoBom)
        
        Write-Host "✓ Fixed $file" -ForegroundColor Green
    }
}

Write-Host "`nDone! Try running run.bat again." -ForegroundColor Green