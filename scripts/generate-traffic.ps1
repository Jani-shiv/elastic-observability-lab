# ─────────────────────────────────────────────────────────────────────────────
# generate-traffic.ps1 — Normal Traffic Generator for Windows PowerShell
# ─────────────────────────────────────────────────────────────────────────────

$BaseUrl = $env:BASE_URL
if (-not $BaseUrl) { $BaseUrl = "http://localhost:8000" }
$SleepSeconds = 1
$RequestCount = 0

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  TicketFlow — Normal Traffic Generator (PowerShell)" -ForegroundColor Cyan
Write-Host "  Target: $BaseUrl" -ForegroundColor White
Write-Host "  Simulating: browse events, view tickets" -ForegroundColor White
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

try {
    while ($true) {
        $RequestCount++
        $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host "[$Timestamp] Session #$RequestCount" -ForegroundColor Green

        # Homepage
        $res = Invoke-WebRequest -Uri "$BaseUrl/" -UseBasicParsing -ErrorAction SilentlyContinue
        Write-Host "  GET /                     → HTTP $($res.StatusCode)"

        # Health
        $res = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -ErrorAction SilentlyContinue
        Write-Host "  GET /health               → HTTP $($res.StatusCode)"

        # Browse all events
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $res = Invoke-WebRequest -Uri "$BaseUrl/api/events" -UseBasicParsing -ErrorAction SilentlyContinue
        $sw.Stop()
        Write-Host "  GET /api/events           → HTTP $($res.StatusCode)  [$($sw.ElapsedMilliseconds)ms]" -ForegroundColor Yellow

        # View individual event details
        foreach ($eventId in 1..3) {
            $res = Invoke-WebRequest -Uri "$BaseUrl/api/events/$eventId" -UseBasicParsing -ErrorAction SilentlyContinue
            Write-Host "  GET /api/events/$eventId       → HTTP $($res.StatusCode)"
        }

        # Ticket lookups
        foreach ($ticketId in @(101, 102, 104)) {
            $res = Invoke-WebRequest -Uri "$BaseUrl/api/tickets/$ticketId" -UseBasicParsing -ErrorAction SilentlyContinue
            Write-Host "  GET /api/tickets/$ticketId     → HTTP $($res.StatusCode)"
        }

        Write-Host ""
        Start-Sleep -Seconds $SleepSeconds
    }
} finally {
    Write-Host "Traffic generator stopped." -ForegroundColor Red
}
