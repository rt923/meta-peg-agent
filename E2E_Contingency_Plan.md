# MCP 链路 E2E 验证应急预案

> 版本: v1.0（2026-08-13）
> 覆盖范围: 13 智能体 MCP 接入链路中已识别的所有风险项
> 来源: E2E_Verification_Report_20260813.md + E2E_Verification_Plan_FlowyAIPC_Cursor.md

---

## 一、风险全景

| 编号 | 风险项 | 影响范围 | 严重度 | 概率 | 触发条件 |
|---|---|---|---|---|---|
| R1 | 桥接层 30878 不可达 | 全部智能体 | 高 | 中 | k3d 集群宕机 / Pod 重启 |
| R2 | proxy 协议兼容失败 | 需代理的智能体 | 高 | 中 | 新客户端版本不兼容 |
| R3 | MCP 工具列表为空 | 单个智能体 | 中 | 中 | mcp.json 配置错误 / proxy 未启动 |
| R4 | arguments 解析失败 | 部分智能体 | 中 | 低 | 新客户端传递非标准 arguments 格式 |
| R5 | 协议版本不匹配 | 部分智能体 | 中 | 低 | 客户端使用 2025-11-25 以外的版本 |
| R6 | inputSchema 命名不兼容 | 部分智能体 | 低 | 低 | 新 snake_case 变体 |
| R7 | 配置加密导致参数丢失 | FlowyAIPC / Trae CN | 中 | 中 | UI 注册后环境变量丢失 |
| R8 | stdio 子进程不支持 | 云端 IDE 类 | 中 | 低 | 客户端不支持 fork 子进程 |
| R9 | 双库落库不同步 | 全部智能体 | 低 | 中 | agent-vault 索引层延迟 |
| R10 | Dify 集群不可用 | 全部智能体 | 高 | 低 | 主机重启 / k3d 损坏 |

---

## 二、应急预案

### R1: 桥接层 30878 不可达

**检测方式:**
```bash
curl -sf --max-time 5 http://localhost:30878/health
# 预期: {"status": "ok"}
```

**应急步骤:**

| 步骤 | 操作 | 命令 |
|---|---|---|
| 1 | 检查 k3d 集群状态 | `kubectl get pods -n dify` |
| 2 | 确认 dify-kb-bridge Pod 运行 | `kubectl get pods -n dify -l app=dify-kb-bridge` |
| 3 | 如果 Pod 异常，重启 | `kubectl rollout restart deployment/dify-kb-bridge -n dify` |
| 4 | 临时暴露端口（无需 k3d） | `kubectl port-forward -n dify svc/dify-kb-bridge 30878:8080` |
| 5 | 验证恢复 | `curl http://localhost:30878/health` |

**恢复时间**: 步骤 1-3 约 2 分钟；步骤 4 约 30 秒

**降级方案**: 如果桥接层长时间不可用，绕过桥接层，直接调用 Dify API：
```bash
curl -X POST http://dify-api:5001/v1/datasets/{dataset_id}/documents \
  -H "Authorization: Bearer $DIFY_API_KEY" \
  -d '{"name":"manual","text":"...","indexing_technique":"high_quality"}'
```

---

### R2: proxy 协议兼容失败

**检测方式:**
```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{}},"id":1}' \
  | timeout 5 node ~/mcp-stdio-proxy/index.mjs
# 预期: 返回 protocolVersion 和 capabilities
```

**应急步骤:**

| 步骤 | 操作 | 详情 |
|---|---|---|
| 1 | 识别失败原因 | 检查 proxy 日志: `LOG_LEVEL=debug node index.mjs` |
| 2 | 补充版本号 | 在 `SUPPORTED_VERSIONS` 数组中添加新版本 |
| 3 | 补充命名转换 | 在 `normalizeToolSchema` 中添加新 snake_case 映射 |
| 4 | 补充 arguments 格式 | 在 `normalizeArguments` 中添加新格式处理 |
| 5 | 重启 proxy | 重启智能体或重新加载 MCP 配置 |

**恢复时间**: 5-10 分钟（取决于修复复杂度）

**预防措施**: 维护 `SUPPORTED_VERSIONS`、`normalizeToolSchema`、`normalizeArguments` 的测试用例

---

### R3: MCP 工具列表为空

**检测方式:**
```bash
echo '{"jsonrpc":"2.0","method":"tools/list","id":2}' | timeout 5 node ~/mcp-stdio-proxy/index.mjs
# 预期: 返回 dify_publish 和 dify_retrieve
```

**应急步骤:**

| 步骤 | 操作 | 命令 |
|---|---|---|
| 1 | 检查 proxy 进程 | `ps aux | grep "index.mjs"` |
| 2 | 手动启动 proxy 测试 | `node ~/mcp-stdio-proxy/index.mjs --test` |
| 3 | 检查桥接层连通 | `curl http://localhost:30878/health` |
| 4 | 检查 mcp.json 语法 | `cat ~/.cursor/mcp.json | python -m json.tool` |
| 5 | 重启智能体 | 关闭并重新打开智能体应用 |

**恢复时间**: 2-3 分钟

**针对 FlowyAIPC 的额外步骤:**
- 重新打开 Settings → MCP Servers → 选中 dify-kb-bridge → 点击 Reconnect
- 如果配置丢失，重新输入配置参数

---

### R4: arguments 解析失败

**检测方式:**
```bash
LOG_LEVEL=debug node ~/mcp-stdio-proxy/index.mjs 2>&1 | grep "raw arguments"
```

**应急步骤:**

| 步骤 | 操作 | 详情 |
|---|---|---|
| 1 | 确认 arguments 格式 | 从 debug 日志中提取 raw arguments |
| 2 | 修复 normalizeArguments | 添加对应的格式转换逻辑 |
| 3 | 运行单元测试 | 用新格式参数测试 `normalizeArguments` |
| 4 | 重启 proxy | 重新加载 MCP 配置 |

**恢复时间**: 5 分钟

**已知格式**: 字符串 JSON、嵌套对象、Base64 编码 → 当前仅处理字符串 JSON

---

### R5: 协议版本不匹配

**检测方式:**
```bash
LOG_LEVEL=debug node ~/mcp-stdio-proxy/index.mjs 2>&1 | grep "protocolVersion"
```

**应急步骤:**

| 步骤 | 操作 | 详情 |
|---|---|---|
| 1 | 获取客户端版本号 | 从 debug 日志中提取 |
| 2 | 添加到 SUPPORTED_VERSIONS | 在 `index.mjs` 的 `SUPPORTED_VERSIONS` 数组中追加 |
| 3 | 重启 proxy | 重新加载 MCP 配置 |

**恢复时间**: 2 分钟

**已知版本**: `2024-11-05`（标准）、`2025-11-25`（Trae CN）

---

### R6: inputSchema 命名不兼容

**检测方式:**
```bash
echo '{"jsonrpc":"2.0","method":"tools/list","id":2}' | node index.mjs | grep -o '"input[Ss]chema"'
```

**应急步骤:**

| 步骤 | 操作 | 详情 |
|---|---|---|
| 1 | 确认不兼容的命名 | 从工具列表输出中识别 |
| 2 | 在 normalizeToolSchema 中添加映射 | 新 snake_case → camelCase 转换 |
| 3 | 重启 proxy | 重新加载 MCP 配置 |

**恢复时间**: 3 分钟

---

### R7: 配置加密导致参数丢失（FlowyAIPC / Trae CN）

**检测方式:**
- 工具列表为空，但 proxy 和 bridge 均正常
- 在智能体 UI 中检查 MCP 服务器配置的环境变量字段

**应急步骤:**

| 步骤 | 操作 | 详情 |
|---|---|---|
| 1 | 删除现有 MCP 服务器配置 | Settings → MCP Servers → 删除 dify-kb-bridge |
| 2 | 重新注册 | 按 mcp_servers.yaml 中的配置重新填写 |
| 3 | 避免特殊字符 | 环境变量值中不要使用 `&`、`\|`、`"`、空格 |
| 4 | 保存后立即测试 | tools/list 验证 |
| 5 | 备用方案 | 切换到 SSE 模式绕过配置加密 |

**恢复时间**: 5 分钟

---

### R8: stdio 子进程不支持

**检测方式:**
- 智能体无法启动 MCP 服务器
- 错误日志包含 "spawn" 或 "fork" 相关错误

**应急步骤:**

| 步骤 | 操作 | 命令 |
|---|---|---|
| 1 | 启动 SSE 代理 | `node ~/mcp-stdio-proxy/index.mjs --mode sse --port 30979 &` |
| 2 | 修改客户端配置 | 将 mcp.json 改为 SSE 模式（见 mcp_servers.yaml §5） |
| 3 | 验证 SSE 端点 | `curl http://localhost:30979/sse` |
| 4 | 重启智能体 | 重新加载 MCP 配置 |

**恢复时间**: 3 分钟

**永久方案**: 将 SSE 代理设为系统服务（systemd / launchd），开机自启

---

### R9: 双库落库不同步

**检测方式:**
```bash
# 在 Trae CN 中检索 agent-vault 索引层
dify_retrieve(query="FlowyAIPC E2E", top_k=5, score_threshold=0.3)
# 预期: 命中 agent-vault 中的索引记录
```

**应急步骤:**

| 步骤 | 操作 | 详情 |
|---|---|---|
| 1 | 等待 30 秒 | 索引层同步有延迟（通常 < 30 秒） |
| 2 | 手动触发索引 | 在 Dify 管理后台 → 数据集 → 重新索引 |
| 3 | 检查 bridge 日志 | `kubectl logs -n dify deployment/dify-kb-bridge --tail=50` |
| 4 | 重试检索 | 等待索引完成后重新检索 |

**恢复时间**: 1-2 分钟

---

### R10: Dify 集群不可用

**检测方式:**
```bash
kubectl get pods -n dify
# 预期: 所有 Pod 状态为 Running
```

**应急步骤:**

| 步骤 | 操作 | 命令 |
|---|---|---|
| 1 | 检查 k3d 状态 | `k3d cluster list` |
| 2 | 启动 k3d 集群 | `k3d cluster start dify-local` |
| 3 | 等待 Pod 就绪 | `kubectl wait --for=condition=ready pod -l app=dify-api -n dify --timeout=120s` |
| 4 | 验证 API | `curl http://dify-api:5001/v1/health` |
| 5 | 极端情况重建 | `k3d cluster delete dify-local && k3d cluster create dify-local`（需重新部署） |

**恢复时间**: 步骤 1-3 约 3 分钟；步骤 5 约 15 分钟

---

## 三、应急联系人

| 角色 | 负责范围 | 联系方式 |
|---|---|---|
| 基础设施 | k3d 集群 / Dify / bridge | 团队 DevOps 频道 |
| 代理层 | mcp-stdio-proxy | proxy 仓库 Issues |
| 智能体接入 | 各智能体 MCP 配置 | 各自智能体文档 |

---

## 四、应急演练计划

| 频率 | 演练内容 | 参与方 |
|---|---|---|
| 每月 | R1 桥接层重启恢复 | 基础设施 |
| 每季度 | R2-R6 proxy 协议兼容修复 | 代理层 + 新接入智能体 |
| 每半年 | R10 集群全量重建 | 基础设施 |
| 新智能体接入前 | R7 配置加密、R8 SSE 备选 | 接入方 + 代理层 |

---

## 五、版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-08-13 | 初始版本，覆盖 10 个风险项 |