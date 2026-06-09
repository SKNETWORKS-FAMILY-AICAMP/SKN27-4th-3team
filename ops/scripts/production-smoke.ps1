$ErrorActionPreference = "Stop"

if (-not $env:APP_DOMAIN) {
    throw "APP_DOMAIN must be set before running production smoke checks."
}

$baseUrl = "https://$env:APP_DOMAIN"
Invoke-RestMethod -Method Get -Uri "$baseUrl/healthz"
Invoke-RestMethod -Method Get -Uri "$baseUrl/api/v1/auth/csrf"
