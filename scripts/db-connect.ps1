param(
    [Parameter(Position=0)]
    [string]$Role = "owner",
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# load .env
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=\s]+)=(.+)$') {
            Set-Item -Path "env:$($matches[1])" -Value $matches[2].Trim()
        }
    }
} else {
    Write-Host ".env not found. Copy .env.example to .env first." -ForegroundColor Red
    exit 1
}

$url = if ($Role -eq "user") { 
    $env:APP_DATABASE_URL_PSQL 
} else { 
    $env:DATABASE_URL_PSQL 
}

if (-not $url) {
    Write-Host "URL not found for role: $Role" -ForegroundColor Red
    Write-Host "Check .env file and ensure DATABASE_URL_PSQL or APP_DATABASE_URL_PSQL is set." -ForegroundColor Yellow
    exit 1
}

psql $url @Args