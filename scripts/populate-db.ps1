<#
.SYNOPSIS
  Populate the Db2 database by running the SQL in init/01-init.sql inside the db2 container.

.DESCRIPTION
  This script will ensure the `db2` service is running (via docker-compose), wait until the
  Db2 container reports healthy or the Db2 port is reachable, then exec into the container and
  run the SQL file as the Db2 instance user.

  Usage:
    .\scripts\populate-db.ps1

  Optional parameters (run `-Help` for details).
#>

param(
    [string]$ComposeDir = "..",
    [string]$ServiceName = "db2",
    [string]$SqlFile = "init/01-init.sql",
    [string]$DbName = "users",
    [string]$DbUser = "db2inst1",
    [string]$DbPassword = "password",
    [int]$TimeoutSeconds = 600
)

Set-StrictMode -Version Latest

function Write-Log($msg) { Write-Host "[populate-db] $msg" }

Push-Location $PSScriptRoot/.. | Out-Null

Write-Log "Starting (docker-compose up -d $ServiceName)"
& docker-compose up -d $ServiceName | Out-Null

# get container id for the service
$start = Get-Date
$containerId = $null
while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds -and -not $containerId) {
    try {
        $containerId = (docker-compose ps -q $ServiceName) -replace "\s+", ""
    } catch {
        # ignore and retry
    }
    if (-not $containerId) { Start-Sleep -Seconds 2 }
}

if (-not $containerId) {
    Write-Error "Could not find container id for service '$ServiceName' after waiting $TimeoutSeconds seconds."
    Pop-Location | Out-Null
    exit 1
}

$containerName = (docker ps --filter "id=$containerId" --format "{{.Names}}") -replace "\s+", ""
Write-Log "Found container: $containerName ($containerId)"

# Wait for health status or port responsiveness
Write-Log "Waiting for Db2 to be ready (timeout: $TimeoutSeconds s)"
$elapsed = 0
$ready = $false
while ($elapsed -lt $TimeoutSeconds -and -not $ready) {
    # try health status
    try {
        $health = docker inspect --format '{{.State.Health.Status}}' $containerId 2>$null
    } catch { $health = $null }

    if ($health -and $health -eq 'healthy') {
        Write-Log "Container health is healthy"
        $ready = $true
        break
    }

    # fallback: test host port 50000
    try {
        $portTest = Test-NetConnection -ComputerName 'localhost' -Port 50000 -WarningAction SilentlyContinue
        if ($portTest.TcpTestSucceeded) { $ready = $true; break }
    } catch { }

    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Log "Waiting... $elapsed s"
}

if (-not $ready) {
    Write-Error "Timed out waiting for Db2 readiness after $TimeoutSeconds seconds."
    Pop-Location | Out-Null
    exit 1
}

# Path inside container where the file is mounted by compose
$remoteSqlPath = "/docker-entrypoint-initdb.d/$(Split-Path $SqlFile -Leaf)"

Write-Log "Executing SQL file inside container: $remoteSqlPath"

# Build the db2 command to run as the instance user
$inner = ". /database/config/db2inst1/sqllib/db2profile && db2 connect to $DbName user $DbUser using $DbPassword && db2 -tvf $remoteSqlPath"
$dockerExecCmd = "su - $DbUser -c \"$inner\""

Write-Log "Running: docker exec -i $containerName bash -c '$dockerExecCmd'"

$proc = Start-Process -FilePath docker -ArgumentList @("exec", "-i", $containerName, "bash", "-c", $dockerExecCmd) -NoNewWindow -Wait -PassThru

if ($proc.ExitCode -ne 0) {
    Write-Error "docker exec returned exit code $($proc.ExitCode). Check container logs for details."
    Pop-Location | Out-Null
    exit $proc.ExitCode
}

Write-Log "SQL executed successfully."

Pop-Location | Out-Null
Write-Log "Done."
