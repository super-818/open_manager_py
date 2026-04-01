# Open Manager Install Script
# Create desktop shortcut

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Open Manager - Install Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = $ScriptDir

Write-Host "Project Directory: $ProjectDir" -ForegroundColor Yellow
Write-Host ""

# Get desktop path
$DesktopPath = [Environment]::GetFolderPath("Desktop")
Write-Host "Desktop Path: $DesktopPath" -ForegroundColor Yellow
Write-Host ""

# Create shortcut
$ShortcutPath = Join-Path $DesktopPath "OpenManager.lnk"
$PythonPath = (Get-Command python).Source
$RunScript = Join-Path $ProjectDir "run.py"

Write-Host "Creating desktop shortcut..." -ForegroundColor Cyan

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $PythonPath
    $Shortcut.Arguments = "`"$RunScript`""
    $Shortcut.WorkingDirectory = $ProjectDir
    $Shortcut.Description = "Open Manager - Web Version"
    $Shortcut.Save()
    
    Write-Host "  Desktop shortcut created successfully!" -ForegroundColor Green
    Write-Host "  Shortcut path: $ShortcutPath" -ForegroundColor Gray
} catch {
    Write-Host "  Failed to create shortcut: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  1. Double-click 'OpenManager' shortcut on desktop" -ForegroundColor White
Write-Host "  2. Or run: python run.py" -ForegroundColor White
Write-Host "  3. Open http://127.0.0.1:5000 in browser" -ForegroundColor White
Write-Host ""
