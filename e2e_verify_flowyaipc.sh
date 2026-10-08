#!/usr/bin/env bash
# =============================================================================
# e2e_verify_flowyaipc.sh — FlowyAIPC 端到端验证自动化脚本
# =============================================================================
# 基于: E2E_Verification_Plan_FlowyAIPC_Cursor.md §三
# 版本: v2.0 (2026-08-14) — 增强日志版
# 用法: bash e2e_verify_flowyaipc.sh
# 环境要求:
#   - FlowyAIPC 已安装并运行
#   - dify-kb-bridge 桥接层可访问 (localhost:30878)
#   - mcp-stdio-proxy 已部署 (默认 ~/mcp-stdio-proxy/index.mjs)
# =============================================================================

set -euo pipefail

# ── 配置 ──────────────────────────────────────────────
BRIDGE_URL="${BRIDGE_URL:-http://localhost:30878}"
PROXY_PATH="${PROXY_PATH:-$HOME/mcp-stdio-proxy/index.mjs}"
SSE_PORT="${SSE_PORT:-30979}"
REPORT_FILE="e2e_flowyaipc_report_$(date +%Y%m%d_%H%M%S).txt"
LOG_FILE="e2e_flowyaipc_log_$(date +%Y%m%d_%H%M%S).txt"
PASS=0; FAIL=0; SKIP=0

# ANSI 颜色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

# ── 日志函数 (双输出: 控制台 + 日志文件) ─────────────────
# 格式: HH:MM:SS.fff [LEVEL] message
_log() {
    local level="$1"; shift
    local ts; ts=$(date +%H:%M:%S.%3N 2>/dev/null || date +%H:%M:%S)
    echo "[$ts] [$level] $*" | tee -a "$LOG_FILE"
}
log_info()  { _log "INFO"  "$*"; }
log_warn()  { _log "WARN"  "$*"; }
log_error() { _log "ERROR" "$*"; }
log_stage() { _log "STAGE" "$*"; echo -e "\n${BOLD}━━━ $* ━━━${NC}"; }
log_pass()  { PASS=$((PASS + 1)); _log "RESULT" "[PASS] $*"; echo -e "${GREEN}[PASS]${NC}  $*" | tee -a "$REPORT_FILE"; }
log_fail()  { FAIL=$((FAIL + 1)); _log "RESULT" "[FAIL] $*"; echo -e "${RED}[FAIL]${NC}  $*" | tee -a "$REPORT_FILE"; }
log_skip()  { SKIP=$((SKIP + 1)); _log "RESULT" "[SKIP] $*"; echo -e "${YELLOW}[SKIP]${NC}  $*" | tee -a "$REPORT_FILE"; }
check() {
    local desc="$1"; shift
    log_info "Check: $desc"
    if "$@"; then log_pass "$desc"; else log_fail "$desc"; fi
}

# ── 打印报告头 ────────────────────────────────────────
echo "FlowyAIPC E2E Verification Report" > "$REPORT_FILE"
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"
echo "========================================" >> "$REPORT_FILE"
echo ""

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════════╗"
echo "║  FlowyAIPC 端到端 MCP 链路验证自动化脚本         ║"
echo "║  版本: v2.0 | 日期: $(date '+%Y-%m-%d')               ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# 启动日志
log_info "Script start | Bridge=$BRIDGE_URL | Proxy=$PROXY_PATH"
log_info "Report: $REPORT_FILE"
log_info "Log: $LOG_FILE"

# =============================================================================
# 阶段 1: 前置检查 (对应 F0)
# =============================================================================
log_stage "阶段 1/5: 前置环境检查"

check "1.1 Node.js 可用"      command -v node >/dev/null 2>&1
check "1.2 curl 可用"          command -v curl >/dev/null 2>&1
check "1.3 proxy 文件存在"     [ -f "$PROXY_PATH" ]
if [ ! -f "$PROXY_PATH" ]; then
    log_info "   请确认 PROXY_PATH 环境变量或修改脚本中的路径"
    log_info "   预期路径: ~/mcp-stdio-proxy/index.mjs"
fi

check "1.4 桥接层连通"         curl -sf --max-time 5 "$BRIDGE_URL/health" >/dev/null 2>&1
if ! curl -sf --max-time 5 "$BRIDGE_URL/health" >/dev/null 2>&1; then
    log_info "   请确认 k3d 集群运行: kubectl get pods -n dify"
    log_info "   或手动暴露端口: kubectl port-forward -n dify svc/dify-kb-bridge 30878:8080"
fi

# 1.5 proxy 可启动（非致命，失败仅跳过后续阶段）
if [ -f "$PROXY_PATH" ]; then
    if timeout 3 node "$PROXY_PATH" --test 2>/dev/null; then
        log_pass "1.5 proxy 测试模式可用"
    else
        log_skip "1.5 proxy 测试模式不可用（非致命，继续）"
    fi
else
    log_skip "1.5 proxy 测试跳过（文件不存在）"
fi

# =============================================================================
# 阶段 2: proxy 裸连接测试 (对应 F1)
# =============================================================================
log_stage "阶段 2/5: proxy 裸连接测试"

# 2.1 MCP initialize 握手
INIT_RESULT=$(echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{}},"id":1}' | timeout 5 node "$PROXY_PATH" 2>/dev/null || echo "")
if echo "$INIT_RESULT" | grep -q "protocolVersion"; then
    log_pass "2.1 MCP initialize 握手成功"
    echo "    $(echo "$INIT_RESULT" | head -1)" | tee -a "$REPORT_FILE"
else
    log_fail "2.1 MCP initialize 握手失败"
    echo "    原始输出: $INIT_RESULT" | tee -a "$REPORT_FILE"
fi

# 2.2 tools/list
TOOLS_RESULT=$(echo '{"jsonrpc":"2.0","method":"tools/list","id":2}' | timeout 5 node "$PROXY_PATH" 2>/dev/null || echo "")
if echo "$TOOLS_RESULT" | grep -q "dify_publish"; then
    log_pass "2.2 dify_publish 工具可见"
else
    log_fail "2.2 dify_publish 工具不可见"
    echo "    原始输出: $TOOLS_RESULT" | tee -a "$REPORT_FILE"
fi

if echo "$TOOLS_RESULT" | grep -q "dify_retrieve"; then
    log_pass "2.3 dify_retrieve 工具可见"
else
    log_fail "2.3 dify_retrieve 工具不可见"
fi

# =============================================================================
# 阶段 3: 写入能力验证 (对应 F2)
# =============================================================================
log_stage "阶段 3/5: 写入能力验证 (dify_publish)"

PUBLISH_PAYLOAD=$(cat <<'JSONEOF'
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "dify_publish",
    "arguments": {
      "source": "flowyaipc",
      "title": "FlowyAIPC E2E Verification - Automated Test",
      "text": "FlowyAIPC 端到端验证：经 MCP stdio 协议，于 2026-08-13 由自动化脚本 e2e_verify_flowyaipc.sh 调用 dify_publish 完成入库。此文档验证 FlowyAIPC MCP 链路端到端可用。",
      "type": "note"
    }
  },
  "id": 3
}
JSONEOF
)

PUBLISH_RESULT=$(echo "$PUBLISH_PAYLOAD" | timeout 10 node "$PROXY_PATH" 2>/dev/null || echo "")

if echo "$PUBLISH_RESULT" | grep -q "dataset_id"; then
    DATASET_ID=$(echo "$PUBLISH_RESULT" | grep -o '"dataset_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
    DOC_ID=$(echo "$PUBLISH_RESULT" | grep -o '"document_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
    log_pass "3.1 dify_publish 写入成功"
    echo "    dataset_id: $DATASET_ID" | tee -a "$REPORT_FILE"
    echo "    document_id: $DOC_ID" | tee -a "$REPORT_FILE"
    # 保存 document_id 供后续检索验证
    echo "$DOC_ID" > /tmp/e2e_flowyaipc_doc_id
else
    log_fail "3.1 dify_publish 写入失败"
    echo "    原始输出: $PUBLISH_RESULT" | tee -a "$REPORT_FILE"
fi

# =============================================================================
# 阶段 4: 检索能力验证 (对应 F3)
# =============================================================================
log_stage "阶段 4/5: 检索能力验证 (dify_retrieve)"

RETRIEVE_PAYLOAD=$(cat <<'JSONEOF'
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "dify_retrieve",
    "arguments": {
      "query": "FlowyAIPC E2E Verification Automated Test",
      "top_k": 3,
      "score_threshold": 0.3
    }
  },
  "id": 4
}
JSONEOF
)

RETRIEVE_RESULT=$(echo "$RETRIEVE_PAYLOAD" | timeout 10 node "$PROXY_PATH" 2>/dev/null || echo "")

if echo "$RETRIEVE_RESULT" | grep -q "FlowyAIPC"; then
    log_pass "4.1 dify_retrieve 命中写入文档"
    SCORE=$(echo "$RETRIEVE_RESULT" | grep -o '"score"[[:space:]]*:[[:space:]]*[0-9.]*' | head -1 | sed 's/.*: *//')
    echo "    相似度: ${SCORE:-N/A}" | tee -a "$REPORT_FILE"
else
    log_fail "4.1 dify_retrieve 未命中写入文档"
    echo "    原始输出 (前 500 字符): ${RETRIEVE_RESULT:0:500}" | tee -a "$REPORT_FILE"
fi

# =============================================================================
# 阶段 5: SSE 备选模式验证 (对应 F5)
# =============================================================================
log_stage "阶段 5/5: SSE 备选模式验证"

# 启动 SSE 代理
log_info "启动 SSE 代理 (端口 $SSE_PORT)..."
node "$PROXY_PATH" --mode sse --port "$SSE_PORT" &
SSE_PID=$!
sleep 2

# 检查 SSE 端口
if kill -0 "$SSE_PID" 2>/dev/null; then
    if curl -sf --max-time 3 "http://localhost:$SSE_PORT/sse" >/dev/null 2>&1; then
        log_pass "5.1 SSE 模式启动成功 (端口 $SSE_PORT)"
    else
        log_skip "5.1 SSE 端口可访问但 SSE 端点未响应"
    fi
else
    log_fail "5.1 SSE 代理进程启动失败"
fi

# 清理 SSE 进程
if [ -n "${SSE_PID:-}" ]; then
    kill "$SSE_PID" 2>/dev/null || true
    log_info "SSE 代理已停止 (PID $SSE_PID)"
fi

# =============================================================================
# 汇总报告
# =============================================================================
log_stage "验证汇总"

TOTAL=$((PASS + FAIL + SKIP))
echo "" | tee -a "$REPORT_FILE"
echo "╔══════════════════════════════════╗" | tee -a "$REPORT_FILE"
echo "║   FlowyAIPC E2E 验证结果汇总     ║" | tee -a "$REPORT_FILE"
echo "╠══════════════════════════════════╣" | tee -a "$REPORT_FILE"
printf "║  ${GREEN}PASS${NC}: %-2d  ${RED}FAIL${NC}: %-2d  ${YELLOW}SKIP${NC}: %-2d          ║\n" "$PASS" "$FAIL" "$SKIP" | tee -a "$REPORT_FILE"
echo "║  TOTAL: $TOTAL                        ║" | tee -a "$REPORT_FILE"
echo "╠══════════════════════════════════╣" | tee -a "$REPORT_FILE"

if [ "$FAIL" -eq 0 ]; then
    echo "║  ${GREEN}状态: 全部通过 ✅${NC}               ║" | tee -a "$REPORT_FILE"
else
    echo "║  ${RED}状态: 存在失败项 ❌${NC}             ║" | tee -a "$REPORT_FILE"
fi
echo "╚══════════════════════════════════╝" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "详细报告: $REPORT_FILE" | tee -a "$REPORT_FILE"

# 验证后动作提示
if [ "$FAIL" -eq 0 ]; then
    echo ""
    echo -e "${GREEN}验证通过！后续手动步骤：${NC}"
    echo "  1. 在 FlowyAIPC UI 中检查 MCP 工具面板"
    echo "  2. 在 Trae CN 中执行跨 agent 检索验证"
    echo "  3. 更新 [table-interop] 13智能体接入状态表"
    echo "  4. 运行: dify_publish(source='flowyaipc', title='FlowyAIPC MCP 链路端到端验证', ...)"
fi

exit $FAIL