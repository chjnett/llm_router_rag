param(
    [int]$StartOffset = 0,
    [int]$Total = 300,
    [int]$BatchSize = 50,
    [int]$Retries = 2
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $ProjectRoot ".venv\Scripts\caproute-screen.exe"
$Config = Join-Path $ProjectRoot "configs\p0_screening_300_strong.yaml"
if (-not (Test-Path -LiteralPath $Runner)) { throw "Missing runner: $Runner" }

for ($offset = $StartOffset; $offset -lt ($StartOffset + $Total); $offset += $BatchSize) {
    $completed = $false
    for ($attempt = 1; $attempt -le $Retries; $attempt++) {
        Write-Output "STRONG_BATCH offset=$offset size=$BatchSize attempt=$attempt"
        & $Runner --config $Config --offset $offset --limit $BatchSize --refresh-cache
        if ($LASTEXITCODE -eq 0) {
            $completed = $true
            break
        }
    }
    if (-not $completed) {
        throw "Strong batch failed after $Retries attempts: offset=$offset"
    }
}
