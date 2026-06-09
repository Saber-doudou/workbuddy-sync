# WorkBuddy Sync — 跨设备配置同步工具

> **一键将 WorkBuddy 配置同步到腾讯 IMA 云端 + 微云网盘，或从云端恢复配置到新电脑。**

[![Version](https://img.shields.io/badge/version-7.0-blue.svg)](https://github.com/your-username/workbuddy-sync)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)

## ✨ 功能特性

- 🔄 **双备策略**：IMA 轻量快照 + 微云完整包
- 🎯 **智能变更检测**：轻量指纹前置，无变化秒级跳过
- 📦 **模块化架构**：11 个独立模块，单向依赖，无循环引用
- 🔒 **安全可靠**：微云失败感知 + 3 次指数退避重试
- 🎛️ **灵活配置**：支持自定义备份类别和知识内容目录
- 🧪 **单元测试**：13 个测试覆盖核心功能

## 📋 目录

- [快速开始](#-快速开始)
- [配置说明](#-配置说明)
- [使用方式](#-使用方式)
- [模块架构](#-模块架构)
- [同步范围](#-同步范围)
- [错误状态说明](#-错误状态说明)
- [常见问题](#-常见问题)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/workbuddy-sync.git
cd workbuddy-sync
```

### 2. 运行配置向导

```bash
python setup_wizard.py
```

配置向导将引导您完成：
- 检测 WorkBuddy 配置目录
- 选择需要备份的内容类别
- 配置知识内容目录
- 设置微云备份（可选）

### 3. 配置 IMA 凭证

```bash
mkdir -p ~/.config/ima
echo "your_client_id" > ~/.config/ima/client_id
echo "your_api_key" > ~/.config/ima/api_key
```

凭证获取地址：https://ima.qq.com/agent-interface

### 4. 运行同步

```bash
python sync_to_cloud.py
```

## ⚙️ 配置说明

### 配置文件结构

```
workbuddy-sync/
├── config.py              # 默认配置
├── config.user.py         # 用户自定义配置（优先级更高）
├── setup_wizard.py        # 配置向导
└── ...
```

### 配置项说明

#### 路径配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `WORKBUDDY_DIR` | WorkBuddy 配置目录 | `~/.workbuddy` |
| `CONFIG_DIR` | IMA 配置目录 | `~/.config/ima` |
| `WORKSPACE_DIR` | 工作空间目录 | `~/WorkBuddy` |

#### 备份类别

| 类别 | 说明 | 默认启用 |
|------|------|----------|
| `core` | 核心配置文件 | ✅ |
| `skills` | 技能和插件配置 | ✅ |
| `memory` | 记忆文件 | ✅ |
| `automations` | 自动化配置 | ✅ |
| `connectors` | 连接器配置 | ✅ |
| `workspace` | 工作空间配置 | ✅ |
| `knowledge` | 知识内容 | ❌ |
| `ima_creds` | IMA 凭证 | ✅ |
| `weiyun` | 微云备份 | ❌ |

#### 微云配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ENABLE_WEIYUN` | 启用微云备份 | `False` |
| `WEIYUN_CONNECTOR_DIR` | 微云连接器目录 | - |
| `WEIYUN_SCRIPT_DIR` | 微云脚本目录 | - |
| `WEIYUN_PDIR_KEY` | 微云目录 Key | - |
| `WEIYUN_MAX_BACKUPS` | 微云最大备份数 | `3` |

## 📖 使用方式

### 命令行参数

```bash
python sync_to_cloud.py [选项]
```

| 参数 | 说明 |
|------|------|
| `--dry-run` | 模拟运行，不实际上传 |
| `--health-check` | 健康检查，检测配置完整性 |
| `--force` | 强制同步，跳过变更检测 |
| `--default` | 使用旧版单笔记模式 |
| `--init-slot` | 初始化槽位映射 |
| `--reset` | 重置今天槽位计数器 |
| `--help` | 显示帮助信息 |

### 常用命令

```bash
# 日常同步
python sync_to_cloud.py

# 模拟运行（不实际上传）
python sync_to_cloud.py --dry-run

# 健康检查
python sync_to_cloud.py --health-check

# 强制同步
python sync_to_cloud.py --force

# 初始化槽位
python sync_to_cloud.py --init-slot

# 重置今天槽位
python sync_to_cloud.py --reset
```

### 从云端恢复

```bash
python sync_from_cloud.py
```

⚠️ **恢复会覆盖本地配置**。建议先用 `--dry-run` 确认当前状态。

## 🏗️ 模块架构

```
workbuddy-sync/
├── sync_to_cloud.py          # 入口 + CLI + 主流程编排
├── sync_from_cloud.py        # 从云端恢复
├── setup_wizard.py           # 配置向导
├── config.py                 # 默认配置
├── config.user.py            # 用户自定义配置
├── lib/
│   ├── config.py             # 配置加载
│   ├── ima_api.py            # IMA API 层
│   ├── slot_manager.py       # 槽位管理
│   ├── collector.py          # 数据收集
│   ├── fingerprint.py        # 变更检测
│   ├── cleaner.py            # 备份清理
│   ├── stats.py              # 统计提取
│   ├── memory_manager.py     # Memory 管理
│   ├── weiyun.py             # 微云上传
│   ├── builder.py            # 包构建
│   └── health.py             # 健康检查
├── tests/
│   ├── test_fingerprint.py   # 指纹测试
│   ├── test_memory.py        # Memory 测试
│   └── test_builder.py       # 构建测试
├── README.md                 # 本文件
├── LICENSE                   # 许可证
└── .gitignore                # Git 忽略文件
```

## 📦 同步范围

### 核心配置文件

- `SOUL.md`, `IDENTITY.md`, `USER.md` — 身份配置
- `settings.json`, `argv.json` — 应用设置
- `mcp.json`, `.mcp.json` — MCP 配置
- `models.json` — 模型配置
- `workspace-state.json` — 工作空间状态
- `expert-history.json` — 专家历史
- `slot_mapping.json` — 槽位映射
- `mcp-approvals.json` — MCP 审批
- `word-history.json` — 单词历史
- `user-state.json` — 用户状态
- `.neodata_token` — NeoData 令牌

### 技能和插件

- `skills/` — 自定义技能（每个技能最多 15 个文件，≤50KB）
- `plugins/` — 插件配置

### 记忆和自动化

- `memory/` — 记忆文件
- `automations/` — 自动化配置
- `connectors/` — 连接器配置

### 工作空间

- `workspace.json` — 工作空间配置
- `.workbuddy/memory/` — 工作空间记忆
- `.workbuddy/automations/` — 工作空间自动化

### 知识内容（可选）

- `ai-news/` — AI 新闻
- `daily-why/` — 每日冷知识
- `history-today/` — 历史上的今天

## ❌ 错误状态说明

脚本通过 `[SYNC_RESULT]` 标记输出状态：

| 状态 | 含义 | 处理方式 |
|------|------|----------|
| `SUCCESS` | 双备成功（IMA ✅ 微云 ✅） | 无需处理 |
| `SUCCESS_VERIFIED` | 单笔记模式成功且 hash 验证通过 | 无需处理 |
| `UNCHANGED` | 配置无变更（完整指纹匹配） | 无需处理 |
| `UNCHANGED_LIGHT` | 文件系统无变更（轻量指纹匹配） | 无需处理 |
| `PARTIAL` | 部分成功（IMA ✅ 微云 ❌） | 检查微云连接，下次自动重试 |
| `FAILED` | 同步失败 | 检查错误消息，常见原因：IMA 凭证过期、网络问题 |
| `NO_DATA` | 无内容可同步 | 检查工作空间是否为空 |
| `FATAL_ERROR` | 脚本异常 | 查看 traceback，可能需要更新脚本 |

## 🤔 常见问题

### Q: 如何获取 IMA 凭证？

A: 访问 https://ima.qq.com/agent-interface 注册并获取 `client_id` 和 `api_key`。

### Q: 微云备份失败怎么办？

A: 检查以下几点：
1. 微云连接器是否已配置
2. 微云目录 Key 是否正确
3. 网络连接是否正常
4. 微云存储空间是否充足

### Q: 如何自定义备份内容？

A: 运行配置向导 `python setup_wizard.py`，或手动编辑 `config.user.py` 文件。

### Q: 同步失败如何排查？

A: 
1. 运行健康检查：`python sync_to_cloud.py --health-check`
2. 查看错误消息
3. 检查 IMA 凭证是否过期
4. 检查网络连接

### Q: 如何从云端恢复？

A: 运行 `python sync_from_cloud.py`，按提示选择槽位即可。

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

### 开发规范

- 遵循 PEP 8 代码规范
- 添加适当的注释和文档
- 编写单元测试
- 更新 README.md

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [WorkBuddy](https://github.com/your-username/workbuddy) — 跨设备配置同步工具
- [腾讯 IMA](https://ima.qq.com) — 云端存储服务
- [微云](https://www.weiyun.com) — 网盘服务

## 📞 联系方式

- 作者：Your Name
- 邮箱：your.email@example.com
- GitHub：https://github.com/your-username

---

**享受跨设备同步的便利！** 🎉
