# mcp-stdio-proxy 双模式兼容配置指南

> 版本：v1.0（2026-08-13）
> 适用场景：MCP 客户端协议兼容性桥接，使不支持原生 MCP stdio 的智能体通过代理层接入 Dify 共享知识平面

---

## 一、背景

部分智能体（如 Trae CN）的 MCP 实现与标准 MCP 协议存在以下差异，导致无法直接通过 stdio 调用 `dify-kb-bridge`：

| 差异项 | 标准 MCP | Trae CN 实现 | 影响 |
|---|---|---|---|
| arguments 格式 | JSON 对象 | 裸 JSON 字符串 | 参数解析失败 |
| 协议版本号 | `2024-11-05` | `2025-11-25` | 版本握手失败 |
| inputSchema 命名 | `inputSchema`（驼峰） | `input_schema`（蛇形） | 工具描述未识别 |

`mcp-stdio-proxy` 通过双模式兼容层解决上述差异，使智能体透明接入。

---

## 二、架构概览

```
┌──────────────┐     stdio      ┌────────────────────┐     HTTP      ┌──────────────┐
│  MCP 客户端    │ ←──────────→ │  mcp-stdio-proxy    │ ←──────────→ │  dify-kb-    │
│ (Trae CN等)   │  双模式兼容    │  (index.mjs)        │   localhost   │  bridge      │
│               │               │  port: 动态分配       │   30878       │  (k3d Pod)   │
└──────────────┘               └────────────────────┘              └──────┬───────┘
                                                                          │
                                                                   ┌──────▼───────┐
                                                                   │  Dify API    │
                                                                   │  (k3d Svc)   │
                                                                   └──────────────┘
```

**关键特性：** 双模式（stdio + SSE）、无状态（每次请求独立转发）、零配置（默认从 `BRIDGE_URL` 环境变量读取）

---

## 三、三连坎修复详解

### 3.1 裸 JSON 双模式（arguments 兼容）

**问题**：部分 MCP 客户端传递 `arguments` 时使用 JSON 字符串而非 JSON 对象。

```json
// 标准 MCP（对象）
{"method": "tools/call", "params": {"arguments": {"source": "trae", "text": "..."}}}

// Trae CN（字符串）
{"method": "tools/call", "params": {"arguments": "{\"source\": \"trae\", \"text\": \"...\"}"}}
```

**修复逻辑**：

```javascript
function normalizeArguments(args) {
  if (typeof args === 'string') {
    try {
      return JSON.parse(args);  // 裸 JSON 字符串 → 对象
    } catch (e) {
      return args;  // 非 JSON 字符串原样传递
    }
  }
  return args;  // 已是对象，直接传递
}
```

### 3.2 协议版本回显（2025-11-25 兼容）

**问题**：MCP 握手阶段客户端发送 `2025-11-25` 版本号，标准协议仅识别 `2024-11-05`。

**修复逻辑**：

```javascript
const SUPPORTED_VERSIONS = ['2024-11-05', '2025-11-25'];

function handleInitialize(request) {
  const clientVersion = request.params?.protocolVersion;
  if (SUPPORTED_VERSIONS.includes(clientVersion)) {
    return {
      protocolVersion: clientVersion,  // 回显客户端版本，不做降级
      capabilities: { tools: {} }
    };
  }
  return { protocolVersion: '2024-11-05', capabilities: { tools: {} } };
}
```

### 3.3 inputSchema 驼峰转换

**问题**：MCP 标准使用 `inputSchema`（驼峰），部分客户端实现使用 `input_schema`（蛇形）。

**修复逻辑**：

```javascript
function normalizeToolSchema(tool) {
  if (tool.input_schema && !tool.inputSchema) {
    tool.inputSchema = tool.input_schema;
    delete tool.input_schema;
  }
  if (tool.inputSchema?.properties) {
    for (const [key, prop] of Object.entries(tool.inputSchema.properties)) {
      if (prop.snake_case) {
        prop.snakeCase = prop.snake_case;
        delete prop.snake_case;
      }
    }
  }
  return tool;
}
```

---

## 四、客户端配置

### 4.1 Trae CN（UI 注册）

```
Server Name:  dify-kb-bridge
Command:      node
Arguments:    C:\path\to\mcp-stdio-proxy\index.mjs
Environment:
  BRIDGE_URL=http://localhost:30878
```

> 注意：Trae CN 配置可能以加密形式存储，无法直接编辑配置文件。

### 4.2 Cursor（mcp.json）

```json
{
  "mcpServers": {
    "dify-kb-bridge": {
      "command": "node",
      "args": ["/path/to/mcp-stdio-proxy/index.mjs"],
      "env": {
        "BRIDGE_URL": "http://localhost:30878"
      }
    }
  }
}
```

### 4.3 CodeBuddy CN（mcp.json）

```json
{
  "mcpServers": {
    "dify-kb-bridge": {
      "command": "node",
      "args": ["/path/to/mcp-stdio-proxy/index.mjs"],
      "env": {
        "BRIDGE_URL": "http://localhost:30878"
      }
    }
  }
}
```

### 4.4 通用命令行验证

```bash
# 测试 proxy 是否正常启动
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | node index.mjs

# 预期输出包含 protocolVersion 和 tools 能力声明
```

---

## 五、SSE 模式（备选）

对于不支持 stdio 子进程的智能体（如云端 IDE），可启用 SSE 模式：

```bash
# 启动 SSE 代理（端口 30979）
node index.mjs --mode sse --port 30979

# 客户端配置 SSE 端点
# URL: http://localhost:30979/sse
```

```json
{
  "mcpServers": {
    "dify-kb-bridge": {
      "type": "sse",
      "url": "http://localhost:30979/sse"
    }
  }
}
```

---

## 六、环境变量参考

| 变量 | 默认值 | 说明 |
|---|---|---|
| `BRIDGE_URL` | `http://localhost:30878` | dify-kb-bridge 桥接层地址 |
| `PROXY_MODE` | `stdio` | 运行模式：`stdio` 或 `sse` |
| `SSE_PORT` | `30979` | SSE 模式监听端口 |
| `LOG_LEVEL` | `info` | 日志级别：`debug` / `info` / `warn` / `error` |
| `REQUEST_TIMEOUT` | `30000` | 桥接层请求超时（毫秒） |

---

## 七、排障指南

### 7.1 MCP 工具列表为空

```bash
# 检查 proxy 是否正常启动
node index.mjs --test

# 检查桥接层连通性
curl http://localhost:30878/health
# 预期：{"status": "ok"}
```

### 7.2 arguments 解析报错

```bash
# 开启 debug 日志查看原始 arguments
LOG_LEVEL=debug node index.mjs

# 日志中搜索 "raw arguments" 查看原始格式
# 如果 arguments 是未知格式，需在 normalizeArguments 中添加处理逻辑
```

### 7.3 协议版本不匹配

```bash
# 查看客户端发送的版本号
LOG_LEVEL=debug node index.mjs

# 日志中搜索 "protocolVersion" 确认版本号
# 如果出现新版本号，添加到 SUPPORTED_VERSIONS 数组
```

### 7.4 工具 Schema 字段缺失

```bash
# 检查返回的工具列表
echo '{"jsonrpc":"2.0","method":"tools/list","id":2}' | node index.mjs

# 确认每个工具都有 inputSchema 字段
# 如果缺少，检查 normalizeToolSchema 是否需要处理新的命名变体
```

---

## 八、安全注意事项

- `BRIDGE_URL` 仅绑定 `localhost`（127.0.0.1），不对外暴露
- SSE 模式端口 `30979` 也仅绑定 `localhost`
- 所有凭据通过环境变量注入，不写入配置文件
- proxy 代码勿包含硬编码 token 或密钥