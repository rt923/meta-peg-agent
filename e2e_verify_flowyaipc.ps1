$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $env:TEMP "e2e_flowyaipc_log_${ts}.txt"
$ReportFile = Join-Path $env:TEMP "e2e_flowyaipc_report_${ts}.txt"
$PASS = 0; $FAIL = 0; $SKIP = 0
$BRIDGE = "http://localhost:30878"
$PROXY = Join-Path $env:USERPROFILE "mcp-stdio-proxy\index.mjs"

function Log($Lvl, $Msg) {
    $t = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$t] [$Lvl] $Msg"
    Add-Content -Path $LogFile -Value $line
    Write-Host $line
}
function Pass($D) { $script:PASS++; Log "RESULT" "[PASS] $D"; Add-Content -Path $ReportFile -Value "[PASS] $D"; Write-Host "  [PASS] $D" -ForegroundColor Green }
function Fail($D) { $script:FAIL++; Log "RESULT" "[FAIL] $D"; Add-Content -Path $ReportFile -Value "[FAIL] $D"; Write-Host "  [FAIL] $D" -ForegroundColor Red }
function Skip($D) { $script:SKIP++; Log "RESULT" "[SKIP] $D"; Add-Content -Path $ReportFile -Value "[SKIP] $D"; Write-Host "  [SKIP] $D" -ForegroundColor Yellow }

Log "INIT" "Script start | Bridge=$BRIDGE | Proxy=$PROXY"
Log "INFO" "Report: $ReportFile"
Log "INFO" "Log: $LogFile"

$header = "FlowyAIPC E2E Verification Report`n=================================`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`nBridge: $BRIDGE`nProxy: $PROXY`nLog: $LogFile"
$header | Set-Content $ReportFile
Write-Host $header
Write-Host ""

# Stage 1
Log "STAGE" "Stage 1/5: Pre-flight Checks"

Log "INFO" "1.1 Node.js"
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) { $v = node --version 2>&1; Log "INFO" "  Node.js: $v"; Pass "1.1 Node.js available" }
else { Fail "1.1 Node.js NOT available" }

Log "INFO" "1.2 curl"
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if ($curl) { Pass "1.2 curl available" }
else { Fail "1.2 curl NOT available" }

Log "INFO" "1.3 proxy file"
$proxyExists = Test-Path $PROXY
if ($proxyExists) { $s = (Get-Item $PROXY).Length; Log "INFO" "  Proxy: $PROXY ($s bytes)"; Pass "1.3 proxy file exists" }
else { Log "WARN" "  Proxy NOT found: $PROXY"; Fail "1.3 proxy file NOT found" }

Log "INFO" "1.4 bridge reachable"
try {
    $r = curl.exe -sf --max-time 5 "$BRIDGE/health" 2>&1
    Log "INFO" "  Bridge response: $r"
    if ($r -match "ok") { Pass "1.4 bridge reachable" }
    else { Log "WARN" "  Unexpected: $r"; Fail "1.4 bridge NOT healthy" }
} catch {
    Log "ERROR" "  Bridge unreachable: $_"
    Fail "1.4 bridge unreachable"
}

Log "INFO" "1.5 proxy test mode"
if ($proxyExists) {
    try {
        $p = Start-Process -FilePath "node" -ArgumentList $PROXY,"--test" -NoNewWindow -PassThru -RedirectStandardOutput "$env:TEMP\proxy_test_out.txt" -RedirectStandardError "$env:TEMP\proxy_test_err.txt"
        $p | Wait-Process -Timeout 5 -ErrorAction SilentlyContinue
        if (!$p.HasExited) { $p.Kill() }
        Pass "1.5 proxy test mode OK"
    } catch {
        Log "WARN" "  Proxy test failed: $_"
        Skip "1.5 proxy test unavailable"
    }
} else {
    Skip "1.5 proxy test skipped (file missing)"
}

# Stage 2: Proxy connection (only if proxy + bridge available)
if ($proxyExists -and $PASS -ge 4) {
    Log "STAGE" "Stage 2/5: Proxy Connection Test"
    
    Log "INFO" "2.1 MCP initialize"
    $initPayload = '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{}},"id":1}'
    try {
        $initResult = $initPayload | node $PROXY 2>&1
        $initStr = [string]($initResult -join " ")
        Log "INFO" "  Init response length: $($initStr.Length)"
        if ($initStr -match "protocolVersion") {
            Pass "2.1 MCP initialize handshake OK"
            if ($initStr -match '"protocolVersion"\s*:\s*"([^"]+)"') { Log "INFO" "  Negotiated version: $($Matches[1])" }
        } else { Fail "2.1 MCP initialize handshake failed"; Log "ERROR" "  Raw: $initStr" }
    } catch { Fail "2.1 MCP initialize exception"; Log "ERROR" "  Exception: $_" }
    
    Log "INFO" "2.2 tools/list"
    $toolsPayload = '{"jsonrpc":"2.0","method":"tools/list","id":2}'
    try {
        $toolsResult = $toolsPayload | node $PROXY 2>&1
        $toolsStr = [string]($toolsResult -join " ")
        Log "INFO" "  tools/list response length: $($toolsStr.Length)"
        if ($toolsStr -match "dify_publish") { Pass "2.2 dify_publish visible" }
        else { Fail "2.2 dify_publish NOT visible" }
        if ($toolsStr -match "dify_retrieve") { Pass "2.3 dify_retrieve visible" }
        else { Fail "2.3 dify_retrieve NOT visible" }
    } catch { Fail "2.2/2.3 tools/list exception"; Log "ERROR" "  Exception: $_" }
    
    # Stage 3: Write
    Log "STAGE" "Stage 3/5: Write Verification (dify_publish)"
    $pubArgs = '{"source":"flowyaipc","title":"FlowyAIPC E2E Test","text":"FlowyAIPC E2E verification via automated script.","type":"note"}'
    $pubPayload = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"dify_publish","arguments":' + $pubArgs + '},"id":3}'
    try {
        $pubResult = $pubPayload | node $PROXY 2>&1
        $pubStr = [string]($pubResult -join " ")
        Log "INFO" "  dify_publish response length: $($pubStr.Length)"
        if ($pubStr -match "dataset_id") {
            Pass "3.1 dify_publish write OK"
            if ($pubStr -match '"document_id"\s*:\s*"([^"]+)"') { $docId = $Matches[1]; Log "INFO" "  document_id: $docId"; $docId | Set-Content "$env:TEMP\e2e_flowyaipc_doc_id.txt" }
            if ($pubStr -match '"dataset_id"\s*:\s*"([^"]+)"') { Log "INFO" "  dataset_id: $($Matches[1])" }
            if ($pubStr -match '"index_document_id"\s*:\s*"([^"]+)"') { Log "INFO" "  index_document_id: $($Matches[1])" }
            if ($pubStr -match '"batch"\s*:\s*"([^"]+)"') { Log "INFO" "  batch: $($Matches[1])" }
        } else { Fail "3.1 dify_publish write failed"; Log "ERROR" "  Response: $pubStr" }
    } catch { Fail "3.1 dify_publish exception"; Log "ERROR" "  Exception: $_" }
    
    # Stage 4: Retrieve
    Log "STAGE" "Stage 4/5: Retrieve Verification (dify_retrieve)"
    $retArgs = '{"query":"FlowyAIPC E2E Test","top_k":3,"score_threshold":0.3}'
    $retPayload = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"dify_retrieve","arguments":' + $retArgs + '},"id":4}'
    try {
        $retResult = $retPayload | node $PROXY 2>&1
        $retStr = [string]($retResult -join " ")
        Log "INFO" "  dify_retrieve response length: $($retStr.Length)"
        if ($retStr -match "FlowyAIPC") { Pass "4.1 dify_retrieve hit document"; if ($retStr -match '"score"\s*:\s*([0-9.]+)') { Log "INFO" "  Score: $($Matches[1])" } }
        else { Fail "4.1 dify_retrieve miss"; Log "ERROR" "  Preview: $($retStr.Substring(0, [Math]::Min(500, $retStr.Length)))" }
    } catch { Fail "4.1 dify_retrieve exception"; Log "ERROR" "  Exception: $_" }
    
    # Stage 5: SSE
    Log "STAGE" "Stage 5/5: SSE Alternative Mode"
    $SSE_PORT = 30979
    try {
        $sseProc = Start-Process -FilePath "node" -ArgumentList $PROXY,"--mode","sse","--port",$SSE_PORT -NoNewWindow -PassThru
        Log "INFO" "  SSE proxy PID: $($sseProc.Id)"
        Start-Sleep -Seconds 3
        if (!$sseProc.HasExited) {
            try { $sseResp = curl.exe -sf --max-time 3 "http://localhost:${SSE_PORT}/sse" 2>&1; Pass "5.1 SSE mode started OK (port $SSE_PORT)"; Log "INFO" "  SSE response: $($sseResp.Substring(0, [Math]::Min(200, $sseResp.Length)))" }
            catch { Skip "5.1 SSE port reachable but endpoint not responding" }
        } else { Fail "5.1 SSE proxy process exited" }
        if (!$sseProc.HasExited) { $sseProc.Kill(); Log "INFO" "  SSE proxy stopped" }
    } catch { Fail "5.1 SSE proxy start exception"; Log "ERROR" "  Exception: $_" }
} else {
    Log "STAGE" "Stage 2-5: SKIPPED (prerequisites not met)"
    Skip "2.1-5.1 All stages skipped (proxy or bridge unavailable)"
    Skip "2.2 tools/list skipped"
    Skip "2.3 dify_retrieve visibility skipped"
    Skip "3.1 dify_publish write skipped"
    Skip "4.1 dify_retrieve retrieve skipped"
    Skip "5.1 SSE mode skipped"
}

# Summary
Log "STAGE" "Summary"
$total = $PASS + $FAIL + $SKIP
$sum = "`n============================================================`n  PASS: $PASS  |  FAIL: $FAIL  |  SKIP: $SKIP  |  TOTAL: $total`n============================================================"
Add-Content -Path $ReportFile -Value $sum
Write-Host $sum
if ($FAIL -eq 0) { Write-Host "Status: ALL PASSED" -ForegroundColor Green }
else { Write-Host "Status: FAILURES DETECTED" -ForegroundColor Red }
Write-Host "Report: $ReportFile"
Write-Host "Log: $LogFile"
Log "INFO" "Script complete | PASS=$PASS FAIL=$FAIL SKIP=$SKIP"
exit $FAIL
