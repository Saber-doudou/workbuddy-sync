#!/usr/bin/env python3
"""WorkBuddy Sync — 通用配置模块（脱敏版）"""

import os

# ============================================================
# 路径配置（用户需要根据自己的环境修改）
# ============================================================

# WorkBuddy 配置目录（默认：~/.workbuddy）
WORKBUDDY_DIR = os.environ.get("WORKBUDDY_DIR", os.path.expanduser("~/.workbuddy"))

# IMA 配置目录（默认：~/.config/ima）
CONFIG_DIR = os.environ.get("IMA_CONFIG_DIR", os.path.expanduser("~/.config/ima"))

# WorkBuddy 应用数据目录（Windows）
WORKBUDDY_APP_DATA = os.environ.get(
    "WORKBUDDY_APP_DATA",
    os.path.join(os.environ.get("APPDATA", ""), "WorkBuddy", "User", "workspaceStorage")
)

# 工作空间目录（包含记忆和知识内容）
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", os.path.expanduser("~/WorkBuddy"))

# 工作空间记忆目录
WORKSPACE_MEMORY_DIR = os.path.join(WORKSPACE_DIR, ".workbuddy", "memory")

# 工作空间自动化目录
WORKSPACE_AUTOMATIONS_DIR = os.path.join(WORKSPACE_DIR, ".workbuddy", "automations")

# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# IMA API 配置
# ============================================================

# 同步笔记标题
SYNC_NOTE_TITLE = os.environ.get("SYNC_NOTE_TITLE", "WorkBuddy Sync Backup")

# IMA API 基础 URL
IMA_BASE_URL = os.environ.get("IMA_BASE_URL", "https://ima.qq.com/openapi/note/v1")

# API 超时时间（秒）
API_TIMEOUT = int(os.environ.get("API_TIMEOUT", "30"))

# ============================================================
# 知识内容目录
# ============================================================

# 需要同步的知识内容子目录（可自定义）
KNOWLEDGE_SUBDIRS = os.environ.get("KNOWLEDGE_SUBDIRS", "ai-news,daily-why,history-today").split(",")

# ============================================================
# 备份清理配置
# ============================================================

# 备份最大保留天数
MAX_BACKUP_AGE_DAYS = int(os.environ.get("MAX_BACKUP_AGE_DAYS", "90"))

# 最大备份数量
MAX_BACKUP_COUNT = int(os.environ.get("MAX_BACKUP_COUNT", "10"))

# ============================================================
# 文件瘦身配置
# ============================================================

# 排除的子目录
EXCLUDED_SUBDIRS = {
    "references", "scripts", "assets", "node_modules", "__pycache__",
    "rules", "examples", "templates", "docs", "tests", "__tests__"
}

# 每个技能最大文件数
MAX_FILES_PER_SKILL = int(os.environ.get("MAX_FILES_PER_SKILL", "15"))

# 单个文件最大大小（字节）
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", str(50 * 1024)))  # 50KB

# ============================================================
# 指纹文件配置
# ============================================================

# 完整指纹文件
FINGERPRINT_FILE = os.path.join(WORKBUDDY_DIR, ".sync_fingerprint.json")

# 轻量指纹文件
LIGHT_FINGERPRINT_FILE = os.path.join(WORKBUDDY_DIR, ".sync_light_fingerprint.json")

# ============================================================
# 槽位管理配置
# ============================================================

# 槽位映射文件
SLOT_MAPPING_FILE = os.path.join(WORKBUDDY_DIR, "slot_mapping.json")

# 周一到周五的槽位名称
WEEKDAY_SLOTS = {
    "Mon": "WB_Mon",
    "Tue": "WB_Tue",
    "Wed": "WB_Wed",
    "Thu": "WB_Thu",
    "Fri": "WB_Fri",
}

# 周一到周五的中文名称
WEEKDAY_NAMES = {"Mon": "周一", "Tue": "周二", "Wed": "周三", "Thu": "周四", "Fri": "周五"}

# 每个槽位最大快照数
MAX_SNAPSHOT_COUNT = int(os.environ.get("MAX_SNAPSHOT_COUNT", "15"))

# ============================================================
# Memory 文件配置
# ============================================================

# Memory 文件路径
MEMORY_FILE = os.path.join(WORKSPACE_AUTOMATIONS_DIR, "automation-4", "memory.md")

# 归档天数
ARCHIVE_DAYS = int(os.environ.get("ARCHIVE_DAYS", "30"))

# ============================================================
# 快照构建配置
# ============================================================

# 轻量快照最大大小（字节）
LIGHTWEIGHT_SNAPSHOT_MAX_BYTES = int(os.environ.get("LIGHTWEIGHT_SNAPSHOT_MAX_BYTES", str(900 * 1024)))  # 900KB

# 二进制文件最大大小（字节）
MAX_BINARY_FILE_SIZE = int(os.environ.get("MAX_BINARY_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB

# ============================================================
# 微云配置
# ============================================================

# 微云连接器目录
WEIYUN_CONNECTOR_DIR = os.environ.get(
    "WEIYUN_CONNECTOR_DIR",
    os.path.join(os.path.expanduser("~"), ".workbuddy", "connectors", "your-connector-id")
)

# 微云脚本目录
WEIYUN_SCRIPT_DIR = os.environ.get(
    "WEIYUN_SCRIPT_DIR",
    os.path.join(os.path.expanduser("~"), ".workbuddy", "connectors", "skills", "connector-tencent-weiyun", "scripts")
)

# 微云目录 Key
WEIYUN_PDIR_KEY = os.environ.get("WEIYUN_PDIR_KEY", "your-pdir-key")

# 微云最大备份数
WEIYUN_MAX_BACKUPS = int(os.environ.get("WEIYUN_MAX_BACKUPS", "3"))

# 微云上传超时时间（秒）
WEIYUN_UPLOAD_TIMEOUT = int(os.environ.get("WEIYUN_UPLOAD_TIMEOUT", "300"))

# 微云重试次数
WEIYUN_RETRY_MAX = int(os.environ.get("WEIYUN_RETRY_MAX", "3"))

# 微云重试基础延迟（秒）
WEIYUN_RETRY_BASE_DELAY = int(os.environ.get("WEIYUN_RETRY_BASE_DELAY", "1"))

# 本地最大包数
LOCAL_MAX_PACKAGES = int(os.environ.get("LOCAL_MAX_PACKAGES", "5"))

# ============================================================
# 子项目源代码配置（可自定义）
# ============================================================

# 子项目目录配置示例
PROJECT_SOURCE_DIRS = {
    # 示例：daily-why 项目
    # "daily-why": {
    #     "path": os.path.join(WORKSPACE_DIR, "daily-why"),
    #     "patterns": ["*.py"],
    #     "extra_files": ["topics_context.json", "writing_rules.json"],
    #     "description": "冷知识自动化流水线"
    # },
}

# ============================================================
# 核心备份文件列表（可自定义）
# ============================================================

# 需要备份的核心文件
BACKUP_CORE_FILES = [
    "SOUL.md", "IDENTITY.md", "USER.md",
    "mcp.json", ".mcp.json",
    "settings.json", "argv.json",
    "models.json",
    "workspace-state.json", "expert-history.json",
    "slot_mapping.json", ".sync_fingerprint.json",
    "mcp-approvals.json",
    "word-history.json", "user-state.json",
    ".neodata_token",
]

# 未备份文件说明
NOT_BACKED_UP_FILES = [
    ("workbuddy.db", "自动化引擎数据库 — 已条件性备份（新鲜槽位时含，gzip压缩）", "P1"),
    (".config/ima/client_id + api_key", "IMA 凭证 — 已随备份包同步", "P1"),
    ("connectors/", "连接器认证令牌和 MCP 配置 — 已备份", "P1"),
    ("brain/", "AI 对话历史", "低"),
]

# 未备份项目
NOT_BACKED_UP_PROJECTS = []
