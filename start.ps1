$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCommand) {
    $dockerPath = $dockerCommand.Source
} else {
    $dockerPath = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'
    if (-not (Test-Path -LiteralPath $dockerPath)) {
        $dockerPath = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
    }
}
if (-not (Test-Path -LiteralPath $dockerPath)) {
    throw 'Docker CLI not found. Open Docker Desktop and check its installation path.'
}
if (-not (Test-Path -LiteralPath '.env')) {
    throw 'Missing .env. Copy .env.example to .env and set unique secrets first.'
}

function Invoke-Docker {
    & $dockerPath @args
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed (exit $LASTEXITCODE)." }
}

Invoke-Docker info --format '{{.ServerVersion}}'
Invoke-Docker compose config --quiet
Invoke-Docker compose up --build -d
Invoke-Docker compose exec -T web python manage.py check
Invoke-Docker compose exec -T web python manage.py makemigrations --check --dry-run
Invoke-Docker compose exec -T web python manage.py test

$ready = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        $response = Invoke-WebRequest 'http://localhost:8085/accounts/login/' -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $ready) {
    Invoke-Docker compose logs --tail 60 web
    throw 'The login page did not become ready on port 8085.'
}
Write-Host 'Ready: http://localhost:8085' -ForegroundColor Green
Write-Host 'Create your first login account with: docker compose exec web python manage.py createsuperuser'
