$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ComposeFile = "ops\docker\docker-compose.yml"
$FrontendDir = Join-Path $RepoRoot "frontend"
$FrontendEnvPath = Join-Path $FrontendDir ".env.local"
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
$RetryCount = 12
$RetryDelaySeconds = 2
$FrontendEnvEntries = @(
    "VITE_API_BASE_URL=http://localhost:8000",
    "VITE_WEBSOCKET_BASE_URL=ws://localhost:8000",
    "VITE_WEBSOCKET_CONNECT_TIMEOUT_SECONDS=6"
)

function Assert-RequiredCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name command was not found. Install $Name and check PATH before running local/dev."
    }
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,

        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath $($Arguments -join ' ') failed. exit code: $LASTEXITCODE"
    }
}

function Invoke-WithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,

        [Parameter(Mandatory = $true)]
        [scriptblock] $ScriptBlock
    )

    for ($attempt = 1; $attempt -le $RetryCount; $attempt += 1) {
        try {
            & $ScriptBlock
            return
        } catch {
            if ($attempt -eq $RetryCount) {
                throw "$Name failed. last error: $($_.Exception.Message)"
            }

            Write-Host "$Name retry pending... ($attempt/$RetryCount)"
            Start-Sleep -Seconds $RetryDelaySeconds
        }
    }
}

function Set-FrontendEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,

        [Parameter(Mandatory = $true)]
        [string] $Value
    )

    if (-not (Test-Path -LiteralPath $FrontendEnvPath)) {
        [System.IO.File]::WriteAllText($FrontendEnvPath, "", $Utf8NoBom)
    }

    $content = [System.IO.File]::ReadAllText($FrontendEnvPath, $Utf8NoBom)
    $lines = @()
    if ($content.Length -gt 0) {
        $lines = $content -split "\r?\n"
    }

    $nextLines = New-Object System.Collections.Generic.List[string]
    $found = $false
    $escapedName = [regex]::Escape($Name)
    foreach ($line in $lines) {
        if ($line -match "^$escapedName=") {
            if (-not $found) {
                $nextLines.Add("$Name=$Value")
                $found = $true
            }
            continue
        }

        if ($line.Length -gt 0) {
            $nextLines.Add($line)
        }
    }

    if (-not $found) {
        $nextLines.Add("$Name=$Value")
    }

    $nextContent = ($nextLines -join "`r`n") + "`r`n"
    if ($nextContent -ne $content) {
        [System.IO.File]::WriteAllText($FrontendEnvPath, $nextContent, $Utf8NoBom)
    }
}

Assert-RequiredCommand "docker"
Assert-RequiredCommand "npm"

Push-Location $RepoRoot
try {
    Write-Host "[1/6] Configure frontend\.env.local"
    foreach ($entry in $FrontendEnvEntries) {
        $name, $value = $entry -split "=", 2
        Set-FrontendEnvValue $name $value
    }

    Write-Host "[2/6] Build backend API image"
    Invoke-NativeCommand "docker" @("compose", "-f", $ComposeFile, "build", "api")

    Write-Host "[3/6] Start PostgreSQL, Redis, and API containers"
    Invoke-NativeCommand "docker" @("compose", "-f", $ComposeFile, "up", "-d", "postgres", "redis")
    Invoke-NativeCommand "docker" @("compose", "-f", $ComposeFile, "up", "-d", "api")

    Write-Host "[4/6] Apply Django migrations"
    Invoke-WithRetry "Django migration" {
        Invoke-NativeCommand "docker" @("compose", "-f", $ComposeFile, "exec", "api", "python", "backend/manage.py", "migrate", "--noinput")
    }

    Write-Host "[5/6] Check backend health"
    Invoke-WithRetry "backend healthz" {
        Invoke-RestMethod -Method Get -Uri "http://localhost:8000/healthz" | Out-Null
    }
    Invoke-WithRetry "backend csrf" {
        Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/auth/csrf" | Out-Null
    }

    Write-Host "[6/6] Start frontend Vite dev server"
    Push-Location $FrontendDir
    try {
        if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
            Invoke-NativeCommand "npm" @("ci")
        } else {
            Write-Host "frontend\node_modules already exists; skipping npm ci."
        }

        Write-Host "Browser URL: http://127.0.0.1:5173"
        Write-Host "Static prototype URL: http://127.0.0.1:5173/prototype/game-background.html"
        Invoke-NativeCommand "npm" @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5173", "--strictPort")
    } finally {
        Pop-Location
    }
} finally {
    Pop-Location
}
