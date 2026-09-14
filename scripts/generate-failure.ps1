# ─────────────────────────────────────────────────────────────────────────────
# generate-failure.ps1 — Incident Traffic Generator for Windows PowerShell
# ─────────────────────────────────────────────────────────────────────────────

$BaseUrl = $env:BASE_URL
if (-not $BaseUrl) { $BaseUrl = "http://localhost:8000" }
$SleepSeconds = 1
$RequestCount = 0

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
Write-Host "  TicketFlow — INCIDENT SCENARIO (PowerShell)" -ForegroundColor Red
Write-Host "  Simulating: slow seat-inventory API" -ForegroundColor White
Write-Host "  Target: $BaseUrl/api/events" -ForegroundColor White
Write-Host ""
Write-Host "  ⚠  Make sure SIMULATE_LATENCY=true is set:" -ForegroundColor Yellow
Write-Host "     1. Edit .env -> SIMULATE_LATENCY=true" -ForegroundColor Yellow
Write-Host "     2. docker compose up -d --force-recreate app" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
Write-Host ""

# Verify latency simulation state
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -ErrorAction SilentlyContinue
    if ($health -and $health.simulate_latency -eq $true) {
        Write-Host "✓ Incident mode ACTIVE — seat inventory latency enabled (2-5s delays)" -ForegroundColor Green
    } else {
        Write-Host "⚠ WARNING: simulate_latency is currently DISABLED on the server!" -ForegroundColor Red
        Write-Host "   Set SIMULATE_LATENCY=true in .env and restart app container to test latency." -ForegroundColor Red
    }
} catch {
    Write-Host "Could not reach server at $BaseUrl" -ForegroundColor Red
}

Write-Host ""

try {
    while ($true) {
        $RequestCount++
        $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host -NoNewline "[$Timestamp] Request #$RequestCount -> GET /api/events ... "

        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $res = Invoke-WebRequest -Uri "$BaseUrl/api/events" -UseBasicParsing -ErrorAction Stop
            $sw.Stop()
            Write-Host "HTTP $($res.StatusCode) — $($sw.ElapsedMilliseconds)ms" -ForegroundColor Red
        } catch {
            $sw.Stop()
            Write-Host "FAILED ($($sw.ElapsedMilliseconds)ms)" -ForegroundColor DarkRed
        }

        Start-Sleep -Seconds $SleepSeconds
    }
} finally {
    Write-Host "Incident traffic generator stopped." -ForegroundColor Red
}
