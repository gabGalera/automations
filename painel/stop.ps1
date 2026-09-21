$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$porta = if ($env:PAINEL_API_PORT) { [int]$env:PAINEL_API_PORT } else { 8765 }

Write-Host "Encerrando Painel de Automações..." -ForegroundColor Cyan

$agentes = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match '\s-m\s+agent(\s|$)' }

foreach ($proc in $agentes) {
    Write-Host "  Agente PID $($proc.ProcessId)"
    Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
}

$portaOcupada = Get-NetTCPConnection -LocalPort $porta -State Listen -ErrorAction SilentlyContinue
if ($portaOcupada) {
    $pidPorta = $portaOcupada[0].OwningProcess
    Write-Host "  Porta $porta (PID $pidPorta)"
    Stop-Process -Id $pidPorta -Force -ErrorAction SilentlyContinue
}

$watchers = Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'consolidacao_base_\d+\.watcher' }

foreach ($proc in $watchers) {
    Write-Host "  Watcher PID $($proc.ProcessId): $($proc.CommandLine)"
    Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 1

$resto = @()
try {
    Invoke-RestMethod "http://127.0.0.1:$porta/health" -TimeoutSec 2 | Out-Null
    $resto += "agente ainda responde na porta $porta"
} catch {
    # ok
}

$watchersRestantes = Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'consolidacao_base_\d+\.watcher' }
if ($watchersRestantes) {
    $resto += "$($watchersRestantes.Count) watcher(s) ainda ativo(s)"
}

if ($resto) {
    Write-Host "Aviso: $($resto -join '; ')" -ForegroundColor Yellow
} else {
    Write-Host "Tudo encerrado." -ForegroundColor Green
}
