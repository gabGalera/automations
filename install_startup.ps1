$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms

function Show-Aviso {
    param(
        [string]$Texto,
        [ValidateSet("Info", "Error")]
        [string]$Tipo = "Info"
    )
    $icon = if ($Tipo -eq "Error") {
        [System.Windows.Forms.MessageBoxIcon]::Error
    } else {
        [System.Windows.Forms.MessageBoxIcon]::Information
    }
    [System.Windows.Forms.MessageBox]::Show(
        $Texto,
        "Consolidacao base_1",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        $icon
    ) | Out-Null
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    Show-Aviso -Tipo Error -Texto "pythonw nao encontrado no PATH. Nao foi possivel criar o atalho de inicializacao."
    Write-Error "pythonw nao encontrado no PATH."
}
$startup = [Environment]::GetFolderPath("Startup")
$lnk = Join-Path $startup "consolidacao-base-1.lnk"
try {
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($lnk)
    $sc.TargetPath = $pythonw
    $sc.Arguments = "-m consolidacao_base_1"
    $sc.WorkingDirectory = $root
    $sc.WindowStyle = 7
    $sc.Description = "Watcher consolidacao transacoes/recebiveis base_1"
    $sc.Save()
} catch {
    Show-Aviso -Tipo Error -Texto "Falha ao criar o atalho:`n$($_.Exception.Message)"
    throw
}
Show-Aviso -Tipo Info -Texto "Atalho criado.`n$lnk`nNo login ou ao clicar, abre o painel para ligar/desligar o watcher."
Write-Output "Atalho criado: $lnk"
