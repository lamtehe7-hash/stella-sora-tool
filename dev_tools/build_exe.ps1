# Build ban exe (PyInstaller onedir):
#   dist\app\app.exe — app desktop kieu Alas (pywebview, khong console)  [mac dinh]
#   dist\SST\SST.exe — giao dien web pywebio (them tham so -Web)
# Chay:  powershell -ExecutionPolicy Bypass -File dev_tools\build_exe.ps1 [-Web]
param([switch]$Web)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if ($Web) {
    & "$root\venv\Scripts\pyinstaller.exe" --noconfirm SST.spec
    $out = 'SST'
} else {
    & "$root\venv\Scripts\pyinstaller.exe" --noconfirm app.spec
    $out = 'app'
}

# assets/ phai nam CANH exe (ROOT cua ban frozen = thu muc chua exe)
Copy-Item -Recurse -Force "$root\assets" "$root\dist\$out\assets"
Write-Host "Xong: $root\dist\$out (giu nguyen thu muc assets di kem)"
