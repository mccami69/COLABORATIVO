param(
    [int]$Port = 5000
)

$ErrorActionPreference = 'Stop'

function Test-Admin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host 'Reiniciando como administrador para abrir el firewall...' -ForegroundColor Yellow
    $arguments = @(
        '-NoProfile'
        '-ExecutionPolicy', 'Bypass'
        '-File', $PSCommandPath
        '-Port', $Port
    )
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $arguments
    exit
}

$ruleName = "Flask Cafeteria $Port"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if (-not $existingRule) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null
    Write-Host "Regla de firewall creada para el puerto $Port." -ForegroundColor Green
} else {
    Write-Host "La regla de firewall ya existe para el puerto $Port." -ForegroundColor Green
}

Set-Location $PSScriptRoot
Write-Host "Iniciando servidor..." -ForegroundColor Cyan
python app.py