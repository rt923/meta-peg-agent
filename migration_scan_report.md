# doc_alignment 迁移评估报告

| 属性 | 值 |
|---|---|
| 目标目录 | `C:\Users\1\WorkBuddy\2026-07-13-11-57-54\meta_peg_agent` |
| 扫描时间 | 2026-07-28 18:32:37 |
| 扫描工具 | migration_scanner.py v0.1 |

## 总览

| 维度 | 标签 | 通过 | 失败 | 未知 | 通过率 |
|---|---|---|---|---|---|
| D1 | 实证文档对齐 | 0 | 0 | 14 | 0% |
| D2 | 同性质遗漏扫描 | 0 | 0 | 4 | 0% |
| D3 | 目录树完整性 | 2 | 3 | 0 | 40% |
| D4 | 登记文件交叉引用 | 3 | 1 | 1 | 60% |
| D5 | 运行时产物识别 | 2 | 0 | 3 | 40% |
| D6 | 演进信号回溯 | 0 | 0 | 4 | 0% |
| **总计** | | **7** | **4** | **26** | **19%** |

## D1: 实证文档对齐 (0/14 通过)

| # | 检查项 | 状态 | 详情 |
|---|---|---|---|
| 1.1 | 所有公开函数的参数名在文档中正确列出 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.2 | 所有公开函数的默认参数值在文档中正确标注 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.3 | 所有公开函数的返回值类型在文档中明确标注 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.4 | 文档中声称的函数签名与代码实际签名一一对应 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.5 | 每个 if/else 分支在文档中有对应行为描述 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.6 | 每个异常处理路径在文档中有说明 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.7 | 每个配置选项/开关在文档中有说明 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.8 | 生产代码中的字段名与文档完全一致 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.9 | JSON schema / API 响应字段名与文档一致 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.10 | 文档中的目录树与实际磁盘文件一致 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.11 | 文档中的文件名模板与代码实际产出一致 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.12 | 文档中的数值与实际运行结果一致 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.13 | 文档中描述的行为与代码实际行为一致 | ⚠️ | 需人工检查代码与文档对齐 |
| 1.14 | 文档中的示例代码可实际运行 | ⚠️ | 需人工检查代码与文档对齐 |

## D2: 同性质遗漏扫描 (0/4 通过)

| # | 检查项 | 状态 | 详情 |
|---|---|---|---|
| 2.1 | 是否存在只修了 .md 忘了 .py 的同类偏差 | ⚠️ | 需人工检查代码与文档对齐 |
| 2.2 | 是否存在只修了英文文档忘了中文文档的同类偏差 | ⚠️ | 需人工检查代码与文档对齐 |
| 2.3 | 是否存在只修了 README 忘了 API 文档的同类偏差 | ⚠️ | 需人工检查代码与文档对齐 |
| 2.4 | 是否有已修复的偏差在关联文件中仍有残留旧值 | ⚠️ | 需人工检查代码与文档对齐 |

## D3: 目录树完整性 (2/5 通过)

| # | 检查项 | 状态 | 详情 |
|---|---|---|---|
| 3.1 | 是否有 workspace_map.md 或等效目录树文件 | ✅ | C:\Users\1\WorkBuddy\2026-07-13-11-57-54\meta_peg_agent\workspace_map.md |
| 3.2 | 目录树中的文件数与磁盘实际文件数一致 | ❌ | 目录树 ≈ 59, 磁盘 105 (差 46) |
| 3.3 | 运行时产物未被逐名登记到目录树 | ✅ |  |
| 3.4 | 所有目录树中的文件在磁盘上均存在 | ❌ | 虚假条目: ['domain/', 'agents/', 'orchestrator.prompt.md', 'executor.prompt.md', 'checker.prompt.md', 'challenger.prompt.md', 'active_tools/', 'blind_spot/', 'drift/', 'self_reference/', 'apps/', 'process.prompt.md', 'feedback.prompt.md', 'policy_sync.prompt.md', 'monitor.prompt.md', 'multi_agent.prompt.md', 'state.prompt.md', 'meta_cognition.prompt.md'] |
| 3.5 | 磁盘上的所有源文件在目录树中均有登记 | ❌ | 目录树遗漏: ['.gitignore', 'ARCHITECTURE_BRIEF.md', 'build_historical_index.py', 'ci_lint.py', 'ci_timing_report.json', 'demo_peg_collaboration.py', 'doc_alignment_README.md', 'guardrails_enforce.v0.2.bak.py', 'migration_scanner.py', 'mock_integration_test.py', 'peg_guard_prompt.md', 'peg_team_overview.md', 'peg_trace.py', 'phase0_meta_peg_agent_prompt.md.guardrail.json', 'phase0_meta_peg_agent_prompt_full.md', 'render_mermaid.py', 'run_gate.sh', 'run_tests.ps1', 'stage1_team_prompt.md', 'test_guardrails_readonly.py', 'test_integration_live.py', 'test_llm_config_switch.py', 'test_peg_a_v0_6_flow.py', 'test_peg_trace.py', 'test_r9_runtime.py', 'test_readonly_windows.py', 'test_unlock_hash_check.py', 'verify_mock_helpers.py', 'AUTO_MERGE', 'COMMIT_EDITMSG', 'config', 'description', 'FETCH_HEAD', 'HEAD', 'index', 'ORIG_HEAD', 'pyproject.toml', 'README.md', 'setup.py', 'validate.py', '__init__.py', 'self_modify_001.diff.md', 'self_modify_002.diff.md', 'self_modify_003.diff.md', 'FIX-002-guardrails-readonly-windows.md', 'pre-commit', 'gate_20260714_125558_73_PASS_20bceea9a4fd1304.jsonl', 'gate_20260714_125600_08_REJECT_4f81d002a00e1274.jsonl', 'gate_20260714_130852_03_REJECT_5d7cdda0a9e59a27.jsonl', 'TN-001-llm-readonly-fix.md', '_historical_index.md', '歡迎.md', 'config', 'applypatch-msg.sample', 'commit-msg.sample', 'fsmonitor-watchman.sample', 'post-update.sample', 'pre-applypatch.sample', 'pre-commit.sample', 'pre-merge-commit.sample', 'pre-push.sample', 'pre-rebase.sample', 'pre-receive.sample', 'prepare-commit-msg.sample', 'push-to-checkout.sample', 'sendemail-validate.sample', 'update.sample', 'exclude', 'HEAD', 'master', 'HEAD', 'master', 'cf2e90626c72fb5692d2a71c749d5f14409c0b', '503b3dcb013851d51c5d5ce61440f31c90fe6f', 'c33b1566e3b33aae56ed53470b02406392df5b', '6704cbe49a8eeb6d4c19eea2e51bcf567e3909', '5308bc3f360aeef3c8f213e2d98f41852e70ab', 'a9c09e7878ce3955fdda70975cd80805adc03b', 'a342241667667bb3e9b3820734e08b39a7f77f', '981a71c6c64b2f304883c8d693adac74c9c453', '1eda311982d6515e71232a81e6f4ba16666fce', '78df0fa0d388ac6bd68062092b748fbf395e35', '91e1e5c2c3979b0de743097fce7ada2ca8e21f', 'c8a61a68e600b8b5a0e044519e849066d97d41', '8ffed0cf535748a611c48476b532f768231852', '28186e17c95b44598efe27cd2b85b063a08ea8', '9bb942d05c76f4f93fb681353c7fa023a04a9d', 'd19f32d2cfad2c54ec0e64a32279213b7fbb5b', 'b106719d7df05d2ef1f398d8ba3ca4ea4b960e', '6787481e007d7ad4b3d263912704ff34ef86c5', '85cf262ae02eae4ec766d97d27d0fb8c0fed6e', 'ae386b6c85968c4a0f2efbb455bdd6a021b017', '5a4b7a4a7b2b14c39c33349f9c2d0fbb887d1e', 'c9c2a17a90fcaff547b19e91bce9aa1b2f7d30', '4ba4211e9e0cc061b61a054610bbfa34cef6e2', 'f3f43ab2cf1c72c07c6d2a0f6af200f66717aa', '6d637e68d668208a4077d4fabab6c955a71c03', 'c38b6425ad3dd6a61c072c038097d544b038e8', 'fc29671615182f07f2d4e87a079c5afdb010b4', '19b538971a5d52aa62154e686f10d0094d21f4', '7219b32b4e6ecb41aadd995b8eb0cd5d23dfd2', 'c3f955a0d38d401673c589a31d2202c8fb8d9b', '5d344d34cd0326ddee73ee8f9e4c61d7f3f740', 'a46ecafa5be07ad794ed16685f35e44f55ad29', '1bf011f05e88f71a810829d42bb0aedd4e953d', '2cddd0a53db9304fa077e7d69575f0ca5320fb', '8a71f3ac030c4430c5ef207ead93a383f47944', 'e9f13d9e2febc05c65960a29505b4ef655cdad', '06f426ceaac3491c4ea75c5ba130b783426fec', 'd113b39c092849d14550f4d35452507a124db1', 'c965119ab9f06b6c0efda532a75a7f32f7f302', '3bfee9addbe5db22ab2c1224e4f018b9e59721', 'c32216256f89d82e7e79e0a5c078d5d16454db', 'be1c9efb56091102e63a9c8e1b0a35742bf26d', '3fe73838329d0fe4bddf45e8b6bd24ef3eb391', '4dbfdc57d5c67d0f974c352df4bfa636a9a334', 'b632f5d5eae505582e4eef7b6a296d83052a4a', 'c3f2bbc16dd4d5470347af915013058bc6617b', 'ddded0b66ae194c50bc374e3a153e86c1c7efa', 'ba12c4699dbc6eb709890f5995428e2b3471f5', '0fde0e459ed15ae21766fa872e4df6ae3b8348', 'cd977becaa9ab34aa688c5fe0d60dc6bc0e3ed', '9b90da7172bebbc1a65e30ed0a1c611b5b26dc', 'cb26c57f8c46a11802b63925b44f69c2b06c47', 'a1e4fce52cb22ac728106fd6a26cde388093f2', '0bd41707620dedddc52c276dcf0bac5ccf54c1', '0fde22784e129fb1cb6094167b9b204bf61b5b', 'c09e6c1779adf9b516a81b0265f9ff0ad414f5', 'f346924107c34d8de03df8d6dde630362ec056', '39c1b09b88b30ea3b826099f8b00620d09581d', 'e3b0ba644b6e6387d902d9ef5a1e820d8d2b3a', '3eab085730326e5d2d901c74ed9e83586415d5', 'c6f2bbd3e2ed488c94f41eedb253c1e858a152', '073de6de300ce8c47b1ea1302d64a7146fa690', '1c1e1a316849c6c1e847bd977270d76fd5229c', 'd3e1a7be29dc606468559af9ee94a7a561b752', '8f469e42f2e2ec2db676003d6d909e79b35079', 'e52b5f4b9cfbb790cbaae3a2072b867b0d6ab0', '7ac9949cef753bc65c1758cce5812545c89107', 'b38a5bfba9c6fb9788fd619222d460992e305f', '9ffa45f52dac9e0803bf108d8814782f99c570', 'b25e9fe75733359a6393d1361b7a238b517fec', '6e72956837481db27f4e1c59b07c6d83155355', '26dfeeb6e641a33dae4961196235bdb965b21b', '780320248024f9495aebae620ea446039683a4', '559091c9b92692f8af0ce7447be943c791b572', 'bf59b780902e50eefc575cc156baf9932fd4cf', '5b6724966fa49e0a11d33e8f81f22ae2651a80', 'a4d528c3c61e060a45c766d0190a3ee11ed389', 'dcb1eb0defc41d899fdb744b0b3b894a1524c7', '416d5e13f5a7d4c1aa3e5035950d687250fc65', '615c026a1aa4998e054e782752bf3928d45ce9', '077133ea7fd734ad42bd51df98329ac4821d15', '37c3d3c859d9fc67768f9bd7a610ea9d8c14ae', 'fc9e457b143c0e0c00b3028ed637d1424ee77b', 'ef95583d1241582d35767bee7c71a05759e17c', '76997e454b7a1ee59a1d6e3ba1447f81ca2bdf', 'fec8acb00f345ebbc62ac22fcb2696e30e0d34', 'b15646a1cd27072d622d61fbbbf53157e21722', '8d18d8fe09676d2f3e8be4b28b7603345b6470', '7ae9b849682ed438e02c657e33e4249b961bc4', 'dadd6c564fcc737172d961955bc95a75a0ed1a', '6ddfaaf97ae07d951cb74274712b6a8e5c368b', '4c0a881eb2c4332f8da9121130fc7e6358a0c5', 'f8a5b614e11e651c9cec4be7609aa3ec22bf52', '24fd4f7fc14e2e3ce726b1e41e328df6201801', 'b66c8a8393757d7eeb7c3ef119e1b848f99c76', '39c196b49338194e5bde0f296e7674fb57935f', '09a07e76e130678df3954958f1fd1d8039d314', '8cf59cf82e2ebf2f804ab2ea4e6f108570fdc7', '1f46d2e84d404de54376b2e28a789078145f9b', 'a2223004469a3d3183361b1f3fd4296843e825', '7d8b4b3d50917503378b19187cb0f79fe70a0a', '1eb3ab6c1a6421e06caf4bc890f5dba39a0006', '03eff264075c54529a82edecbcd3dc759eb630', 'ae9b1423e0c6083d882bd0d27e082946a602cc', '111137c4019f8f2454de2cb3e8f3b23a9d178e', '08fd8b6da3df3bcb1e8a9da57f4da5891e0c14', 'ebd812d8e407d76be1eb8dbed13fea78b9cb9f', '1badd8fd9bfba9efaba1e65bc2a70466d67a81', 'cd645d5c3288cf2c79b9ad910d60aa05c9dfb2', 'master', 'HEAD', 'master', 'apply_unlock_hash_check.py', 'apply_v0_5_to_v0_6.py', 'finalize_v0_6.py', 'fix_cap_reg.py', 'run_peg_a_e2e_demo.py', 'update_registries_v0_6.py', 'update_reg_v0_3.py', 'verify_v0_6_applied.py', 'manifest.json', 'reasoning.jsonl', 'manifest.json', 'reasoning.jsonl', '20260721_104251_0b52-e2e-demo-script.md', '20260721_104525_0b52-e2e-demo-script.md', 'app.json', 'appearance.json', 'core-plugins.json', 'graph.json', 'workspace.json'] |

## D4: 登记文件交叉引用 (3/5 通过)

| # | 检查项 | 状态 | 详情 |
|---|---|---|---|
| 4.1 | 是否有 versions.md 或等效版本登记文件 | ✅ | C:\Users\1\WorkBuddy\2026-07-13-11-57-54\meta_peg_agent\versions.md |
| 4.2 | versions.md 中登记的文件在项目目录中实际存在 | ✅ |  |
| 4.3 | 是否有 capability_registry.md 或等效能力登记册 | ✅ | C:\Users\1\WorkBuddy\2026-07-13-11-57-54\meta_peg_agent\capability_registry.md |
| 4.4 | 三份登记文件是否有交叉引用 | ❌ | 三份登记文件无交叉引用 |
| 4.5 | 最近一次变更是否在三份登记文件中同步更新 | ⚠️ | 需人工检查最近提交记录 |

## D5: 运行时产物识别 (2/5 通过)

| # | 检查项 | 状态 | 详情 |
|---|---|---|---|
| 5.1 | 日志文件是否用通配模式覆盖 | ⚠️ | 需人工检查日志通配 |
| 5.2 | trace/artifacts 产物是否用通配覆盖 | ⚠️ | 需人工检查 trace 通配 |
| 5.3 | 缓存目录是否被排除 | ✅ | 缓存目录未排除 |
| 5.4 | IDE 配置目录是否用目录级注释处理 | ⚠️ | 需人工检查 IDE 配置注释 |
| 5.5 | 通配模式是否统一使用正斜杠 / | ✅ |  |

## D6: 演进信号回溯 (0/4 通过)

| # | 检查项 | 状态 | 详情 |
|---|---|---|---|
| 6.1 | 最近一次变更的修复范围是否准确登记 | ⚠️ | 需人工检查代码与文档对齐 |
| 6.2 | 最近一次变更的回归验证结果是否写入登记条目 | ⚠️ | 需人工检查代码与文档对齐 |
| 6.3 | 演进信号计数是否与变更次数一致 | ⚠️ | 需人工检查代码与文档对齐 |
| 6.4 | 是否有未登记的变更 | ⚠️ | 需人工检查代码与文档对齐 |

## 优先级建议

🔴 **P0 立即**: 存在真偏差或目录树虚假条目，立即修复
🟠 **P1 本周**: 登记基础设施缺失，本周补齐
🟡 **P2 本月**: 文档质量提升，本月内完成
