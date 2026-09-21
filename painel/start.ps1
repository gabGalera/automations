$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$web = Join-Path $root "web"
$dist = Join-Path $web "dist"

function Test-Comando($nome) {
    return [bool](Get-Command $nome -ErrorAction SilentlyContinue)
}

Set-Location $root

if (-not (Test-Comando "python")) {
    Write-Error "python não encontrado no PATH"
}
if (-not (Test-Comando "npm")) {
    Write-Error "npm não encontrado no PATH"
}

if (-not (Test-Path $dist)) {
    Write-Host "Frontend ausente — buildando..." -ForegroundColor Cyan
    Set-Location $web
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run build
    Set-Location $root
}

$porta = if ($env:PAINEL_API_PORT) { [int]$env:PAINEL_API_PORT } else { 8765 }
$ocupada = Get-NetTCPConnection -LocalPort $porta -State Listen -ErrorAction SilentlyContinue
if ($ocupada) {
    $pid = $ocupada[0].OwningProcess
    Write-Host "Porta $porta em uso (PID $pid)." -ForegroundColor Yellow
    $resposta = Read-Host "Encerrar processo e continuar? [s/N]"
    if ($resposta -match '^[sS]') {
        Stop-Process -Id $pid -Force
        Start-Sleep -Seconds 1
    } else {
        Write-Host "Cancelado. Use outra porta: `$env:PAINEL_API_PORT=8766; .\start.ps1"
        exit 1
    }
}

Write-Host "Subindo agente em http://127.0.0.1:$porta" -ForegroundColor Green
python -m agent
