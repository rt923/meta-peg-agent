# registry_tools CLI 使用手册

## 概述

`registry_tools` 提供三个 CLI 命令，用于维护项目登记册（`versions.md` 和 `workspace_map.md`）与磁盘文件的一致性。

| 命令 | 功能 | 对应脚本 |
|---|---|---|
| `registry-check` | 扫描并报告不一致（只读） | `fix_versions_refs.py` |
| `registry-fix` | 扫描并自动修复不一致 | `fix_versions_refs.py` |
| `registry-register` | 扫描并补登未登记文件 | `auto_register_versions.py` |

---

## 安装

```bash
# 从 wheel 包安装
pip install registry_tools-0.1.0-py3-none-any.whl

# 或从源码安装
cd registry_tools
pip install -e .
```

安装后，三个命令自动注册到系统 PATH：

```bash
registry-check --help
registry-fix --help
registry-register --help
```

---

## 一、registry-check — 登记册一致性扫描

### 功能

扫描 `workspace_map.md` 目录树、`versions.md` 工程化产物表与磁盘实际文件，报告三类问题：

| 检查项 | 编号 | 说明 |
|---|---|---|
| 虚假条目 | 3.4 | `workspace_map.md` 中登记但磁盘上不存在的文件 |
| 遗漏文件 | 3.5 | 磁盘上存在但 `workspace_map.md` 中未登记的文件 |
| 引用不一致 | — | `versions.md` 中登记但磁盘不存在 / 磁盘存在但未登记 |

### 参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|---|---|---|---|---|
| `--target` | `-t` | `PATH` | 当前工作目录 | 要扫描的目标项目目录 |
| `--dry-run` | — | `flag` | `True`（默认开启） | 仅报告差异，不修改任何文件 |
| `--fix` | — | `flag` | `False` | 自动修复 `workspace_map.md`（与 `--dry-run` 互斥） |

### 退出码

| 退出码 | 含义 |
|---|---|
| `0` | 扫描完成（可能有发现的问题） |
| `1` | 致命错误：`workspace_map.md` 或 `versions.md` 不存在 |

### 使用示例

```bash
# 1. 扫描当前目录（只读）
registry-check --dry-run

# 2. 扫描指定项目目录
registry-check --target /path/to/project --dry-run

# 3. 使用简写参数
registry-check -t ./my-project --dry-run

# 4. 仅输出日志到文件（便于 CI 存档）
registry-check -t ./project --dry-run 2>check.log

# 5. 模块方式运行（未安装 pip 包时）
python -m registry_tools.fix_versions_refs --target ./project --dry-run
```

### 输出示例

```
🔍 扫描目标: /path/to/project
   workspace_map.md: /path/to/project/workspace_map.md
   versions.md: /path/to/project/versions.md

   目录树条目: 11
   versions.md 条目: 3
   磁盘文件数: 15

── 3.4 虚假条目（目录树登记但磁盘不存在）: 3
   L8: ghost.py
   L9: deprecated/old_module.py
   L11: legacy_config.json

── 3.5 遗漏文件（磁盘存在但目录树未登记）: 5
   config.json
   new_feature.py
   drafts/wip.md
   scripts/deploy.sh
   tests/test_new.py

── versions.md 引用检查:
   登记但磁盘不存在: 0
   磁盘存在但未登记: 5
   ⚠️ config.json
   ⚠️ new_feature.py

💡 运行 --fix 以自动修复上述问题

✅ 扫描完成
```

---

## 二、registry-fix — 登记册自动修复

### 功能

与 `registry-check` 相同的扫描逻辑，但会**自动修复** `workspace_map.md`：
- 移除虚假条目
- 补登遗漏文件到目录树末尾

> ⚠️ **注意**：`registry-fix` 只修复 `workspace_map.md`，不修改 `versions.md`。`versions.md` 的补登请使用 `registry-register`。

### 参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|---|---|---|---|---|
| `--target` | `-t` | `PATH` | 当前工作目录 | 要修复的目标项目目录 |
| `--fix` | — | `flag` | `False` | 必须显式指定，执行修复 |

### 退出码

| 退出码 | 含义 |
|---|---|
| `0` | 修复完成 |
| `1` | 致命错误 |

### 使用示例

```bash
# 1. 修复当前目录的 workspace_map.md
registry-fix --target ./project --fix

# 2. 修复后立即验证
registry-fix -t ./project --fix && registry-check -t ./project --dry-run

# 3. 模块方式运行
python -m registry_tools.fix_versions_refs --target ./project --fix
```

### 输出示例

```
🔍 扫描目标: /path/to/project
   ...

🔧 执行修复...
   ✅ workspace_map.md 已修复（移除 3 虚假, 添加 5 遗漏）

✅ 扫描完成
```

---

## 三、registry-register — 文件自动补登

### 功能

扫描磁盘上的合法源文件，将未登记项补登到 `versions.md` 的「工程化产物」表中。

**补登规则**：
- ✅ 补登合法源文件：`.py` `.md` `.json` `.sh` `.ps1` `.toml` `.yml` `.yaml` `.jsonl` `.txt` `.cfg` `.ini` `.diff` `.patch` `.gitignore` `pre-commit`
- ❌ 排除运行时产物：`logs/gate_*.jsonl`、`traces/<trace_id>/*`
- ❌ 排除非源文件：`.png` `.csv` `.pyc` 等
- ❌ 排除自身：`versions.md`、`workspace_map.md`

### 参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|---|---|---|---|---|
| `--target` | `-t` | `PATH` | 当前工作目录 | 要扫描的目标项目目录 |
| `--dry-run` | — | `flag` | `True`（默认开启） | 仅列出待补登文件，不修改 |
| `--apply` | — | `flag` | `False` | 执行补登到 `versions.md` |
| `--date` | — | `STR` | 当天日期 `YYYY-MM-DD` | 补登日期（写入表格的日期列） |

### 退出码

| 退出码 | 含义 |
|---|---|
| `0` | 扫描/补登完成 |
| `1` | 致命错误：`versions.md` 不存在 |

### 使用示例

```bash
# 1. 预览待补登文件（只读）
registry-register --target ./project --dry-run

# 2. 执行补登
registry-register --target ./project --apply

# 3. 使用自定义日期
registry-register -t ./project --apply --date 2026-01-15

# 4. 补登后验证一致性
registry-register -t ./project --apply && registry-check -t ./project --dry-run

# 5. 模块方式运行
python -m registry_tools.auto_register_versions --target ./project --apply
```

### 输出示例

```
🔍 扫描目标: /path/to/project
   versions.md: /path/to/project/versions.md

   磁盘文件数: 15
   已登记条目: 3

── 待补登文件: 5
   ➕ config.json
   ➕ drafts/wip.md
   ➕ new_feature.py
   ➕ scripts/deploy.sh
   ➕ tests/test_new.py

🔧 执行补登 (日期: 2026-08-04)...
   ✅ 已补登 5 个文件到 versions.md

💡 运行 registry-check --target /path/to/project --dry-run 验证一致性
```

---

## 典型工作流

### 新成员加入项目后

```bash
# 1. 检查当前登记册状态
registry-check -t ./project --dry-run

# 2. 如果发现遗漏文件，补登到 versions.md
registry-register -t ./project --apply

# 3. 如果发现虚假条目，修复 workspace_map.md
registry-fix -t ./project --fix

# 4. 最终验证：应无问题
registry-check -t ./project --dry-run
```

### CI/CD 集成

```yaml
# GitHub Actions 示例
- name: 登记册一致性检查
  run: |
    pip install registry_tools-0.1.0-py3-none-any.whl
    registry-check --target . --dry-run 2>registry-check.log
    # 如果发现未登记文件，CI 告警（不自动修复）
```

### 发布前检查清单

```bash
# 一键完整检查
registry-check -t . --dry-run \
  && registry-register -t . --dry-run \
  && echo "✅ 登记册一致性检查通过"
```

---

## 日志系统

三个命令均内置详细日志，默认输出到 stderr。详见 [LOGGING.md](./LOGGING.md)。

### 快速使用

```bash
# 分离日志和业务输出
registry-check -t ./project --dry-run >output.txt 2>debug.log

# 仅看日志（调试模式）
registry-check -t ./project --dry-run 1>/dev/null

# 仅看业务输出
registry-check -t ./project --dry-run 2>/dev/null
```

---

## 测试

```bash
# 运行单元测试
python -m pytest test_registry_tools_cli.py -v

# 使用 mock 项目测试
python setup_mock_project.py
cd test_mock_project
registry-check -t . --dry-run
registry-register -t . --dry-run
```

---

## 常见问题

### 基础问题

#### Q: registry-check 报 "workspace_map.md 不存在"

A: 确认 `--target` 指向的是项目根目录，该目录下应包含 `workspace_map.md` 和 `versions.md`。如果项目确实没有这两个文件，需要先创建空白登记册。

#### Q: 为什么 .png 文件没有被补登？

A: `registry-register` 只补登合法源文件（`.py` `.md` `.json` 等），非源文件（图片、CSV 等）被自动排除。完整的源文件扩展名白名单见补登规则。

#### Q: 为什么 logs/ 下的文件被标记为"遗漏"但 registry-register 不补登？

A: `registry-check` 的 3.5 检查项报告所有磁盘存在但目录树未登记的文件（包括非源文件），但 `registry-register` 只补登合法源文件。运行时产物（`logs/gate_*.jsonl`）会被自动排除。

#### Q: --fix 和 --apply 有什么区别？

A: `--fix`（`registry-fix`）修复 `workspace_map.md`（目录树），`--apply`（`registry-register`）补登 `versions.md`（工程化产物表）。两者互不重叠，通常先 `--apply` 再 `--fix`。

#### Q: 如何自定义排除规则？

A: 编辑对应脚本中的 `EXCLUDE_RUNTIME_PATTERNS`（运行时产物排除）和 `SOURCE_EXTENSIONS`（源文件扩展名白名单）。修改后重新打包 wheel 即可。

---

### 权限与安全

#### Q: registry-fix 或 registry-register 执行时提示 "Permission denied"

A: 检查以下权限：
1. `versions.md` 和 `workspace_map.md` 是否可写 — 使用 `ls -la`（Linux）或文件属性（Windows）确认
2. 项目目录是否在受保护的系统路径下 — 避免在 `/usr/`、`C:\Program Files\` 等目录运行
3. Git 仓库中文件是否被锁定 — 如有 pre-commit hook 做了文件保护，需先解除

```bash
# Linux: 检查文件权限
ls -la versions.md workspace_map.md

# 如果不可写，添加写权限
chmod +w versions.md workspace_map.md
```

#### Q: 如何在只读文件系统或 Docker 容器中运行？

A: `--dry-run` 模式完全只读，不修改任何文件，可以在任何环境下安全运行：

```bash
# Dockerfile 中集成
RUN pip install registry_tools
RUN registry-check --target /app --dry-run
```

如果必须在容器中执行 `--fix` 或 `--apply`，确保目标文件在可写层（volume mount 或 COPY 后的层）。

#### Q: 如何防止 CI 中误执行 --fix 或 --apply？

A: 最佳实践：
1. CI 中**只运行 `--dry-run`**，由人工审核后手动执行修复
2. 如需自动修复，在 CI 中创建新分支提交，而非直接推送到主分支

```yaml
# 安全做法：CI 只检查不修复
- name: 登记册检查
  run: registry-check --target . --dry-run

# 不安全做法（避免）：
# registry-fix --target . --fix  # 直接修改主分支文件
```

#### Q: 团队成员没有 PyPI 安装权限怎么办？

A: 无需 PyPI 权限即可使用：
1. 从共享目录复制 wheel 文件手动安装
2. 从源码安装：`pip install -e /path/to/registry_tools`
3. 直接运行模块：`python -m registry_tools.fix_versions_refs --target . --dry-run`

---

### CI/CD 集成

#### Q: 如何在 GitHub Actions 中集成？

A: 完整示例：

```yaml
name: 登记册一致性检查

on:
  pull_request:
    paths:
      - '**.py'
      - '**.md'
      - '**.json'
      - 'versions.md'
      - 'workspace_map.md'

jobs:
  registry-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: 安装 registry_tools
        run: |
          pip install registry_tools \
            --index-url https://artifactory.YOUR-COMPANY.com/artifactory/api/pypi/pypi-local/simple/

      - name: 登记册一致性检查
        run: |
          registry-check --target . --dry-run 2>registry-check.log
          echo "## 登记册检查结果" >> $GITHUB_STEP_SUMMARY
          cat registry-check.log >> $GITHUB_STEP_SUMMARY

      - name: 上传检查日志
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: registry-check-log
          path: registry-check.log
```

#### Q: 如何在 GitLab CI 中集成？

A:

```yaml
registry-check:
  stage: validate
  image: python:3.12
  before_script:
    - pip install registry_tools
      --index-url https://artifactory.YOUR-COMPANY.com/artifactory/api/pypi/pypi-local/simple/
  script:
    - registry-check --target . --dry-run 2>registry-check.log
    - cat registry-check.log
  artifacts:
    when: always
    paths:
      - registry-check.log
    expire_in: 7 days
  only:
    - merge_requests
```

#### Q: 如何在 Jenkins 中集成？

A:

```groovy
stage('登记册检查') {
    steps {
        sh '''
            pip install registry_tools --index-url ${INTERNAL_PYPI_URL}
            registry-check --target . --dry-run 2>registry-check.log
            cat registry-check.log
        '''
        // 检查日志中是否有未登记文件
        script {
            def log = readFile('registry-check.log')
            if (log.contains('磁盘存在但未登记')) {
                unstable('存在未登记文件，请运行 registry-register --apply')
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'registry-check.log', fingerprint: true
        }
    }
}
```

#### Q: 如何配置 pre-commit hook 自动检查？

A: 在 `.pre-commit-config.yaml` 中添加：

```yaml
repos:
  - repo: local
    hooks:
      - id: registry-check
        name: 登记册一致性检查
        entry: registry-check --target . --dry-run
        language: system
        pass_filenames: false
        always_run: true
        verbose: true
```

安装 hook：

```bash
pre-commit install
pre-commit run registry-check --all-files
```

#### Q: 如何让 CI 失败时自动通知责任人？

A: 在 GitHub Actions 中结合 issue 或 Slack 通知：

```yaml
- name: 通知责任人
  if: failure()
  uses: slackapi/slack-github-action@v2
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    webhook-type: incoming-webhook
    payload: |
      {
        "text": "⚠️ 登记册检查失败: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
      }
```

#### Q: 如何在 CI 中缓存 registry_tools 安装？

A:

```yaml
# GitHub Actions
- name: 缓存 pip 包
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-registry-tools-${{ runner.os }}-${{ hashFiles('.github/workflows/*.yml') }}

# GitLab CI
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - .cache/pip
```

#### Q: CI 中如何只检查变更文件？

A: 结合 `git diff` 只检查有变更的目录：

```bash
# 仅检查变更涉及的项目目录
CHANGED_DIRS=$(git diff --name-only origin/main...HEAD | xargs -I{} dirname {} | sort -u)

for dir in $CHANGED_DIRS; do
    if [ -f "$dir/versions.md" ]; then
        echo "检查 $dir ..."
        registry-check --target "$dir" --dry-run
    fi
done
```

#### Q: registry-check 在 CI 中的退出码含义？

A: `registry-check` 的退出码只表示**命令是否成功执行**，不表示**是否发现问题**：
- `0` = 扫描完成（可能有或没有发现问题）
- `1` = 致命错误（缺少必要文件）

如需在发现问题时让 CI 失败，需额外检查输出：

```bash
registry-check --target . --dry-run 2>check.log
if grep -q "磁盘存在但未登记" check.log; then
    echo "❌ 存在未登记文件"
    exit 1
fi
```