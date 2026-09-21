$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-Comando($nome) {
    return [bool](Get-Command $nome -ErrorAction SilentlyContinue)
}

Write-Host "Verificando pre-requisitos do Painel..." -ForegroundColor Cyan

$ok = $true
foreach ($cmd in @("node", "npm", "python")) {
    if (Test-Comando $cmd) {
        Write-Host "  OK  $cmd"
    } else {
        Write-Host "  FALTA  $cmd" -ForegroundColor Red
        $ok = $false
    }
}

Write-Host ""
Write-Host "Instalando dependencias..." -ForegroundColor Cyan
Set-Location $root
pip install -r agent/requirements.txt
Set-Location "$root\web"
npm install
npm run build

if ($ok) {
    Write-Host ""
    Write-Host "Pronto. Para subir:" -ForegroundColor Green
    Write-Host "  python -m agent   (na pasta painel/)"
    Write-Host "  Abra http://127.0.0.1:8765 no navegador"
    Write-Host ""
    Write-Host "Dev com hot-reload:" -ForegroundColor Green
    Write-Host "  Terminal 1: python -m agent"
    Write-Host "  Terminal 2: cd web && npm run dev  -> http://localhost:5173"
}
