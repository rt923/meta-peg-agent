# 多智能体 MCP 链路端到端验证对比报告

> 报告日期：2026-08-13
> 检索来源：Dify 知识库（Obsidian Vault / TRAE / agent-vault）
> 查询词：「端到端验证 MCP 链路 调用」「Trae CN 原生 MCP dify_publish 入库」
> 命中记录：16 条 | 端到端验证类：6 条

---

## 一、端到端验证记录总览

| # | 智能体 | 日期 | 协议 | 文档名 | 数据集 | 相似度 | 接入序 |
|---|---|---|---|---|---|---|---|
| 1 | **WorkBuddy** | 2026-08-12 | stdio | 13智能体↔共享平面 MCP 接入设计（首例） | agent-vault | 0.62 | 第 1 |
| 2 | **CodeBuddy CN** | 2026-08-12 | stdio | 经原生 MCP 协议接入验证（第二个写入 agent） | agent-vault | 0.72 | 第 2 |
| 3 | **CodeBuddy CN** | 2026-08-12 | SSE | SSE Proxy E2E Verification | agent-vault | 0.55 | (同体) |
| 4 | **TRAE** | 2026-08-12 | 未知 | TRAE 智能体产物示例（检索闭环） | TRAE | 0.42 | 第 3 |
| 5 | **Trae CN** | 2026-08-13 | stdio | PEG-A Trae CN 原生 MCP 链路端到端验证 | TRAE | 0.79 | **第 4** |
| 6 | **Trae CN** | 2026-08-13 | stdio | PEG-A FAQ 记忆维护（首个活体产物） | TRAE | 0.44 | (同体) |

---

## 二、四代验证演进对比

| 对比维度 | WorkBuddy（第1代） | CodeBuddy CN（第2代） | TRAE（第3代） | Trae CN（第4代） |
|---|---|---|---|---|
| **验证方式** | 设计文档 + 实际写入 | 独立 E2E 验证文档 | 产物检索闭环验证 | 原生 MCP 直接调用 dify_publish |
| **协议路径** | stdio → bridge → Dify | stdio → bridge → Dify | 未知 | mcp-stdio-proxy（双模式兼容）→ bridge → Dify |
| **代理层** | 无代理 | 无代理 | 未知 | mcp-stdio-proxy（裸 JSON 双模式 / 协议版本回显 / inputSchema 驼峰） |
| **验证粒度** | 能写入 | 能写入 | 能写入 + 能检索 | 能写入 + 能检索 + 双库落库 + 索引层同步 |
| **技术难点** | 基础连通性 | stdio 协议兼容 | 跨 agent 检索闭环 | 三连坎修复后首次真实调用 |
| **相似度分** | 0.62 | 0.72 | 0.42 | 0.79 |
| **文档类型** | 设计文档 | 验证文档 | 产物示例 | 验证文档 + 索引层 + FAQ 记忆 |

---

## 三、关键发现

### 3.1 接入顺序验证链路完整

```
WorkBuddy（首例）→ CodeBuddy CN（第2）→ TRAE（第3）→ Trae CN（第4）
```

与 13 智能体接入状态表一致，Trae CN 从「待部署」升级为「已验证」。

### 3.2 Trae CN 是唯一需要代理层的智能体

前两个（WorkBuddy、CodeBuddy CN）原生 stdio 直连，Trae CN 因协议兼容问题需经 `mcp-stdio-proxy` 桥接：

- **裸 JSON 双模式**：支持 MCP 规范中 `arguments` 字段的字符串和对象两种形式
- **协议版本回显 2025-11-25**：兼容 Trae CN 的 MCP 协议版本号
- **inputSchema 驼峰**：修复 `input_schema` vs `inputSchema` 命名差异

这增加了链路复杂度但也验证了代理层的健壮性。

### 3.3 相似度趋势

Trae CN 本次验证记录以 **0.79** 分位居最高，与 "mcp-stdio-proxy" / "dify_publish" / "端到端" 等关键词高度匹配，语义检索质量良好。

### 3.4 双库落库验证

本次同时写入 TRAE 专属库（`80a8566f`）和 agent-vault 索引层（`2292f304`），实现跨库可检索，这是前几代未验证的能力。

### 3.5 缺口分析

13 个智能体中仅 4 个完成端到端验证，尚有 **9 个待验证**：

| 状态 | 智能体 | 数量 |
|---|---|---|
| 已验证 | WorkBuddy、CodeBuddy CN、TRAE、Trae CN | 4 |
| 已部署待验证 | Cursor | 1 |
| 待部署 | FlowyAIPC、Work CN、QClaw | 3 |
| 待架构 | 扣子、元宝、Notion、ima | 4 |
| 不适用 | OrcaTerm（云端终端）、Ollama（推理后端） | 2 |

---

## 四、数据质量评估

| 指标 | 值 |
|---|---|
| 总检索记录 | 16 条 |
| 端到端验证类 | 6 条（37.5%） |
| 重复/索引层 | 3 条（agent-vault 索引同步） |
| 非验证类（设计/图片/表格） | 7 条 |
| 平均相似度 | 0.58 |
| 跨库覆盖 | 3/3 数据集均有命中 |

---

## 五、下一步行动

1. **优先验证**：Cursor（已部署，15 分钟可完成）和 FlowyAIPC（需部署，30 分钟）
2. **跟进验证**：Work CN、QClaw（需先完成部署）
3. **架构设计**：扣子、元宝、Notion、ima 的 SSE 暴露方案
4. **更新状态表**：每次验证后更新 `[table-interop] 13智能体接入状态表`
5. **代理层文档**：完善 mcp-stdio-proxy 双模式兼容配置指南