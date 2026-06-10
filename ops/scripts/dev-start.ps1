[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [int]$PostgresPort = 55432,
    [int]$RedisPort = 56379,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepositoryRoot = Resolve-Path (Join-Path $ScriptRoot "..\..")
$FrontendRoot = Join-Path $RepositoryRoot "frontend"
$OutputRoot = Join-Path $RepositoryRoot "output"
$BackendPidFile = Join-Path $OutputRoot "dev-start-backend.pid"
$FrontendPidFile = Join-Path $OutputRoot "dev-start-frontend.pid"
$BackendOutLog = Join-Path $OutputRoot "dev-start-backend.out.log"
$BackendErrLog = Join-Path $OutputRoot "dev-start-backend.err.log"
$FrontendOutLog = Join-Path $OutputRoot "dev-start-frontend.out.log"
$FrontendErrLog = Join-Path $OutputRoot "dev-start-frontend.err.log"
$VenvPython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
$PostgresContainer = "skn27_local_postgres"
$RedisContainer = "skn27_local_redis"
$PostgresPassword = "pilot"

function Write-Step {
    param([string]$Message)
    Write-Host "[dev-start] $Message"
}

function Resolve-CommandPath {
    param(
        [string]$Name,
        [string]$InstallHint
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "$Name command was not found. $InstallHint"
    }
    return $command.Source
}

function Test-TcpPort {
    param([int]$Port)

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $asyncResult = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $asyncResult.AsyncWaitHandle.WaitOne(500)) {
            return $false
        }
        $client.EndConnect($asyncResult)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Wait-ForPort {
    param(
        [int]$Port,
        [string]$Name,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-TcpPort -Port $Port) {
            return
        }
        Start-Sleep -Milliseconds 500
    }
    throw "$Name port did not open: 127.0.0.1:$Port"
}

function Stop-ProcessFromPidFile {
    param([string]$PidFile)

    if (-not (Test-Path $PidFile)) {
        return
    }

    $rawPid = (Get-Content -Path $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $rawPid) {
        return
    }

    $processId = [int]$rawPid
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        return
    }

    Write-Step "Stopping previous dev-start process. PID=$processId"
    Stop-Process -Id $processId -Force
}

function Stop-OwnedPortProcess {
    param(
        [int]$Port,
        [string[]]$AllowedCommandLineFragments
    )

    $connections = Get-NetTCPConnection -LocalAddress "127.0.0.1" -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $processId = [int]$connection.OwningProcess
        if ($processId -le 0) {
            continue
        }

        $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
        $commandLine = if ($null -eq $processInfo) { "" } else { [string]$processInfo.CommandLine }
        $isOwnedDevProcess = $false
        foreach ($fragment in $AllowedCommandLineFragments) {
            if ($commandLine -like "*$fragment*") {
                $isOwnedDevProcess = $true
                break
            }
        }

        if (-not $isOwnedDevProcess) {
            throw "Port $Port is already used by an unrelated process. PID=$processId"
        }

        Write-Step "Stopping existing dev-start port owner. Port=$Port PID=$processId"
        Stop-Process -Id $processId -Force
    }
}

function Stop-ExistingDevServers {
    Stop-ProcessFromPidFile -PidFile $BackendPidFile
    Stop-ProcessFromPidFile -PidFile $FrontendPidFile
    Stop-OwnedPortProcess `
        -Port $BackendPort `
        -AllowedCommandLineFragments @("backend.config.asgi:application", "$RepositoryRoot")
    Stop-OwnedPortProcess `
        -Port $FrontendPort `
        -AllowedCommandLineFragments @("vite", "$FrontendRoot")
}

function Start-OrReuseContainer {
    param(
        [string]$Name,
        [string]$Image,
        [string[]]$RunOptions,
        [string[]]$CommandArguments = @()
    )

    $existingName = docker ps -a --filter "name=^/$Name$" --format "{{.Names}}"
    if ($existingName -eq $Name) {
        $runningName = docker ps --filter "name=^/$Name$" --format "{{.Names}}"
        if ($runningName -ne $Name) {
            Write-Step "Starting $Name container."
            docker start $Name | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to start $Name container."
            }
        }
        else {
            Write-Step "$Name container is already running."
        }
        return
    }

    Write-Step "Creating $Name container."
    docker run -d --name $Name @RunOptions $Image @CommandArguments | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create $Name container."
    }
}

function Initialize-PathForWindows {
    # Windows can expose both Path and PATH; Start-Process may reject duplicate env keys.
    [System.Environment]::SetEnvironmentVariable("PATH", $null, "Process")

    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $frontendBin = Join-Path $FrontendRoot "node_modules\.bin"
    $nodeDefaultPath = "C:\Program Files\nodejs"
    $env:Path = "$frontendBin;$nodeDefaultPath;$machinePath;$userPath"
}

function Ensure-PythonEnvironment {
    if (Test-Path $VenvPython) {
        return
    }

    Write-Step "Creating .venv."
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pythonLauncher) {
        & py -3.14 -m venv (Join-Path $RepositoryRoot ".venv")
        if ($LASTEXITCODE -eq 0) {
            return
        }
        & py -3 -m venv (Join-Path $RepositoryRoot ".venv")
        return
    }

    $python = Resolve-CommandPath -Name "python" -InstallHint "Install Python 3.14 or the Python launcher (py)."
    & $python -m venv (Join-Path $RepositoryRoot ".venv")
}

function Install-Dependencies {
    if ($SkipInstall) {
        Write-Step "Skipping dependency installation."
        return
    }

    Write-Step "Checking Python dependencies."
    & $VenvPython -m pip install -r (Join-Path $RepositoryRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install Python dependencies."
    }

    $npmCmd = Resolve-CommandPath -Name "npm.cmd" -InstallHint "Install Node.js LTS."
    Push-Location $FrontendRoot
    try {
        Write-Step "Running npm ci."
        & $npmCmd ci
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install frontend dependencies."
        }
    }
    finally {
        Pop-Location
    }
}

function Start-Dependencies {
    Resolve-CommandPath -Name "docker" -InstallHint "Install and start Docker Desktop." | Out-Null

    Start-OrReuseContainer `
        -Name $PostgresContainer `
        -Image "pgvector/pgvector:pg17" `
        -RunOptions @(
            "-e", "POSTGRES_DB=pilot",
            "-e", "POSTGRES_USER=pilot",
            "-e", "POSTGRES_PASSWORD=$PostgresPassword",
            "-p", "127.0.0.1:${PostgresPort}:5432"
        )

    Start-OrReuseContainer `
        -Name $RedisContainer `
        -Image "redis:7.4-alpine" `
        -RunOptions @(
            "-p", "127.0.0.1:${RedisPort}:6379"
        ) `
        -CommandArguments @(
            "redis-server", "--appendonly", "no", "--save", ""
        )

    Wait-ForPort -Port $PostgresPort -Name "PostgreSQL"
    Wait-ForPort -Port $RedisPort -Name "Redis"
}

function Set-BackendEnvironment {
    $env:DJANGO_ENV = "local"
    $env:DJANGO_DEBUG = "true"
    $env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"
    $env:DJANGO_CSRF_TRUSTED_ORIGINS = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort"
    $env:DJANGO_CORS_ALLOWED_ORIGINS = $env:DJANGO_CSRF_TRUSTED_ORIGINS
    $env:DJANGO_SECURE_COOKIES = "false"
    $env:POSTGRES_DB = "pilot"
    $env:POSTGRES_USER = "pilot"
    $env:POSTGRES_PASSWORD = $PostgresPassword
    $env:POSTGRES_HOST = "127.0.0.1"
    $env:POSTGRES_PORT = "$PostgresPort"
    $env:REDIS_URL = "redis://127.0.0.1:$RedisPort/0"
    $env:LLM_DISABLED = "true"
}

function Apply-Migrations {
    Write-Step "Applying DB migrations."
    & $VenvPython (Join-Path $RepositoryRoot "backend\manage.py") migrate --noinput
    if ($LASTEXITCODE -ne 0) {
        throw "DB migration failed."
    }
}

function Start-Backend {
    if (Test-TcpPort -Port $BackendPort) {
        throw "Backend port is already in use: 127.0.0.1:$BackendPort"
    }

    Write-Step "Starting Backend ASGI server."
    $process = Start-Process `
        -FilePath $VenvPython `
        -ArgumentList @(
            "-m", "uvicorn",
            "backend.config.asgi:application",
            "--host", "127.0.0.1",
            "--port", "$BackendPort"
        ) `
        -WorkingDirectory $RepositoryRoot `
        -RedirectStandardOutput $BackendOutLog `
        -RedirectStandardError $BackendErrLog `
        -WindowStyle Hidden `
        -PassThru
    Set-Content -Path $BackendPidFile -Value $process.Id
    Wait-ForPort -Port $BackendPort -Name "Backend"
}

function Start-Frontend {
    if (Test-TcpPort -Port $FrontendPort) {
        throw "Frontend port is already in use: 127.0.0.1:$FrontendPort"
    }

    $npmCmd = Resolve-CommandPath -Name "npm.cmd" -InstallHint "Install Node.js LTS."
    Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:VITE_WEBSOCKET_BASE_URL -ErrorAction SilentlyContinue
    $env:SKN27_BACKEND_TARGET = "http://127.0.0.1:$BackendPort"

    Write-Step "Starting Frontend Vite server."
    $process = Start-Process `
        -FilePath $npmCmd `
        -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "$FrontendPort") `
        -WorkingDirectory $FrontendRoot `
        -RedirectStandardOutput $FrontendOutLog `
        -RedirectStandardError $FrontendErrLog `
        -WindowStyle Hidden `
        -PassThru
    Set-Content -Path $FrontendPidFile -Value $process.Id
    Wait-ForPort -Port $FrontendPort -Name "Frontend"
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
Initialize-PathForWindows
Ensure-PythonEnvironment
Stop-ExistingDevServers
Install-Dependencies
Start-Dependencies
Set-BackendEnvironment
Apply-Migrations
Start-Backend
Start-Frontend

Write-Host ""
Write-Host "Dev servers are running."
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
Write-Host "Backend health: http://127.0.0.1:$BackendPort/healthz"
Write-Host "Backend log: $BackendErrLog"
Write-Host "Frontend log: $FrontendOutLog"
