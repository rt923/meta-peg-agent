# FlowyAIPC & Cursor 端到端验证执行计划

> 基于 2026-08-13 多智能体 MCP 链路端到端验证对比报告的缺口分析
> 当前已验证：WorkBuddy（第1）→ CodeBuddy CN（第2）→ TRAE（第3）→ Trae CN（第4）
> 待验证：FlowyAIPC、Cursor、Work CN、QClaw、Notion、扣子、元宝、ima 等 9 个

---

## 一、当前状态

| 智能体 | 接入状态 | 传输协议 | 前置条件 | 复杂度 |
|---|---|---|---|---|
| **Cursor** | 已部署 | stdio | `mcp.json` 已就位，配置已完成 | 低 |
| **FlowyAIPC** | 待部署 | UI 注册 | 配置加密，需手动配置 | 中 |

---

## 二、Cursor 端到端验证计划

### 2.1 前置检查（预计 5 分钟）

```bash
# 确认 mcp.json 配置存在
cat ~/.cursor/mcp.json

# 应包含类似以下内容：
{
  "mcpServers": {
    "dify-kb-bridge": {
      "command": "node",
      "args": ["path/to/mcp-stdio-proxy/index.mjs"],
      "env": {
        "BRIDGE_URL": "http://localhost:30878"
      }
    }
  }
}
```

- [ ] Cursor 中 MCP 工具列表可见 `dify_publish` 和 `dify_retrieve`
- [ ] 桥接层 `dify-kb-bridge` 正在运行（`curl http://localhost:30878/health`）
- [ ] Dify 集群正常（`kubectl get pods -n dify`）

### 2.2 验证步骤（预计 10 分钟）

| 步骤 | 操作 | 验证点 | 预期结果 |
|---|---|---|---|
| **C1** | 在 Cursor 对话中输入：`"调用 dify_publish 写入一条 Cursor E2E 验证记录，source=cursor"` | Cursor 调用 MCP 工具 | 无报错，返回 `dataset_id` + `document_id` |
| **C2** | 在 Cursor 对话中输入：`"调用 dify_retrieve 搜索刚才写入的验证记录，query='Cursor E2E'"` | 检索命中 | 返回刚写入的文档，相似度 > 0.7 |
| **C3** | 在 Trae CN 对话中检索：`"调用 dify_retrieve 搜索 query='Cursor E2E'"` | 跨 agent 检索 | 命中 Cursor 写入的文档 |
| **C4** | 检查 agent-vault 索引层 | 双库落库 | agent-vault 中出现 Cursor 验证记录 |

### 2.3 成功标准

```
✅ C1: dify_publish 写入成功
✅ C2: 同 agent 检索命中
✅ C3: 跨 agent（Trae CN）检索命中
✅ C4: agent-vault 索引层同步
```

### 2.4 风险与应对

| 风险 | 概率 | 应对 |
|---|---|---|
| Cursor 不识别 MCP 工具 | 低 | 重启 Cursor，检查 `mcp.json` 语法 |
| stdio 协议版本不兼容 | 低 | Cursor 原生支持 stdio，无需 proxy |
| 桥接层 30878 不可达 | 中 | 确认 k3d 集群运行，`kubectl port-forward` 临时暴露 |

---

## 三、FlowyAIPC 端到端验证计划

### 3.1 前置部署（预计 15 分钟）

FlowyAIPC 通过 UI 注册 MCP 服务器，配置需加密存储。

**步骤 1 — 获取 mcp-stdio-proxy 路径：**

```bash
ls ~/mcp-stdio-proxy/index.mjs
```

**步骤 2 — 在 FlowyAIPC UI 中注册：**

```
1. 打开 FlowyAIPC → Settings → MCP Servers
2. 点击 "Add Server"
3. 填写配置：
   - Name: dify-kb-bridge
   - Command: node
   - Arguments: /path/to/mcp-stdio-proxy/index.mjs
   - Environment:
     BRIDGE_URL=http://localhost:30878
4. 点击 "Save"（配置将自动加密存储）
5. 确认 MCP 服务器状态为 "Connected"
```

### 3.2 验证步骤（预计 15 分钟）

| 步骤 | 操作 | 验证点 | 预期结果 |
|---|---|---|---|
| **F1** | 检查 FlowyAIPC 工具面板 | MCP 工具可见性 | `dify_publish` / `dify_retrieve` 出现在工具列表 |
| **F2** | 调用 `dify_publish` 写入验证记录，`source=flowyaipc` | 写入能力 | 返回 `dataset_id` + `document_id` |
| **F3** | 调用 `dify_retrieve` 搜索 `query='FlowyAIPC E2E'` | 检索能力 | 命中刚写入的文档 |
| **F4** | 在 Trae CN 中检索：`"dify_retrieve query='FlowyAIPC E2E'"` | 跨 agent 检索 | 命中 FlowyAIPC 写入的文档 |
| **F5** | 检查 agent-vault 索引层 | 双库落库 | agent-vault 中出现 FlowyAIPC 验证记录 |

### 3.3 成功标准

```
✅ F1: MCP 工具可见
✅ F2: dify_publish 写入成功
✅ F3: 同 agent 检索命中
✅ F4: 跨 agent 检索命中
✅ F5: agent-vault 索引层同步
```

### 3.4 风险与应对

| 风险 | 概率 | 应对 |
|---|---|---|
| UI 注册后 MCP 服务器不连接 | 中 | 检查 node 路径、proxy 路径、BRIDGE_URL；查看 FlowyAIPC 日志 |
| 配置加密导致参数丢失 | 中 | 重新输入环境变量，避免特殊字符 |
| FlowyAIPC 不支持 stdio 子进程 | 低 | 切换为 SSE 模式（启动 proxy 时加 `--mode sse --port 30979`） |
| 桥接层不可达 | 中 | 同 Cursor 方案 |

---

## 四、统一验证模板

验证完成后，使用以下模板写入知识库：

```
[AgentName] 端到端验证：经 MCP [stdio|SSE] 协议，于 [YYYY-MM-DD HH:MM] 在 [AgentName] 内
对话直接调用 dify_publish 完成入库。经 dify_retrieve 跨 agent 检索验证通过。
此文档验证 [AgentName] MCP 链路端到端可用。
```

### 写入命令：

```
dify_publish(
    source="cursor" | "flowyaipc",
    title="[AgentName] MCP 链路端到端验证",
    text="<上述模板内容>",
    type="note"
)
```

---

## 五、时间线

| 阶段 | 智能体 | 预计耗时 | 累计 |
|---|---|---|---|
| 第 1 批 | Cursor | 15 分钟 | 15 分钟 |
| 第 2 批 | FlowyAIPC | 30 分钟 | 45 分钟 |
| 验证后 | 更新 13 智能体接入状态表 | 5 分钟 | 50 分钟 |

---

## 六、验证后动作

- [ ] 更新 `[table-interop] 13智能体接入状态表` 中 Cursor 和 FlowyAIPC 的状态为「已验证」
- [ ] 将两条验证记录写入 Dify 知识库
- [ ] 更新 E2E 对比报告，纳入第 5、6 条验证记录
- [ ] 将验证过程中发现的问题记录到 `mcp-stdio-proxy` 排障文档