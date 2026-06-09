#!/usr/bin/env python3
"""WorkBuddy Sync — 配置向导

交互式配置向导，帮助用户快速设置同步配置。
"""

import os
import sys
import json
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           WorkBuddy Sync 配置向导 v1.0                      ║
║                                                              ║
║  本向导将帮助您配置 WorkBuddy 配置同步功能。                  ║
║  请按照提示完成配置。                                        ║
╚══════════════════════════════════════════════════════════════╝
""")

def get_user_input(prompt, default=None, required=True):
    """获取用户输入"""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        if user_input or not required:
            return user_input
        print("  ⚠️  此项为必填项，请重新输入。")

def ask_yes_no(question, default=True):
    """询问是否问题"""
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{question} [{hint}]: ").strip().lower()
        if not answer:
            return default
        if answer in ['y', 'yes', '是', '对']:
            return True
        if answer in ['n', 'no', '否', '不']:
            return False
        print("  ⚠️  请输入 y 或 n")

def detect_workbuddy_dir():
    """检测 WorkBuddy 配置目录"""
    # Windows
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            wb_dir = os.path.join(appdata, "WorkBuddy")
            if os.path.exists(wb_dir):
                return wb_dir
    
    # 默认路径
    home = Path.home()
    wb_dir = home / ".workbuddy"
    if wb_dir.exists():
        return str(wb_dir)
    
    return None

def detect_workspace_dir():
    """检测工作空间目录"""
    # 常见位置
    common_paths = [
        Path.home() / "WorkBuddy",
        Path.home() / "Documents" / "WorkBuddy",
        Path("D:/WorkBuddy"),
        Path("F:/WorkBuddy"),
    ]
    
    for path in common_paths:
        if path.exists():
            return str(path)
    
    return None

def select_backup_categories():
    """让用户选择需要备份的内容类别"""
    print("\n📦 请选择需要备份的内容类别：")
    print("（输入 y 表示需要备份，n 表示跳过）\n")
    
    categories = [
        {
            "id": "core",
            "name": "核心配置文件",
            "description": "SOUL.md, USER.md, settings.json 等",
            "default": True
        },
        {
            "id": "skills",
            "name": "技能 (Skills)",
            "description": "自定义技能和插件配置",
            "default": True
        },
        {
            "id": "memory",
            "name": "记忆 (Memory)",
            "description": "对话记忆和学习记录",
            "default": True
        },
        {
            "id": "automations",
            "name": "自动化 (Automations)",
            "description": "定时任务和自动化配置",
            "default": True
        },
        {
            "id": "connectors",
            "name": "连接器 (Connectors)",
            "description": "OAuth 凭证和 MCP 配置",
            "default": True
        },
        {
            "id": "workspace",
            "name": "工作空间配置",
            "description": "workspace.json 和工作空间设置",
            "default": True
        },
        {
            "id": "knowledge",
            "name": "知识内容",
            "description": "ai-news, daily-why, history-today 等",
            "default": False
        },
        {
            "id": "ima_creds",
            "name": "IMA 凭证",
            "description": "client_id 和 api_key",
            "default": True
        },
        {
            "id": "weiyun",
            "name": "微云备份",
            "description": "上传到微云网盘（需要已配置微云连接器）",
            "default": False
        },
    ]
    
    selected = []
    for cat in categories:
        choice = ask_yes_no(f"  {cat['name']} - {cat['description']}", cat['default'])
        if choice:
            selected.append(cat['id'])
            print(f"    ✅ 已选择: {cat['name']}")
        else:
            print(f"    ⏭️  跳过: {cat['name']}")
    
    return selected

def select_knowledge_subdirs(workspace_dir):
    """让用户选择需要同步的知识内容子目录"""
    if not workspace_dir:
        return []
    
    print("\n📚 检测到的知识内容目录：")
    
    potential_dirs = ["ai-news", "daily-why", "history-today", "notes", "docs"]
    existing_dirs = []
    
    for dirname in potential_dirs:
        dirpath = os.path.join(workspace_dir, dirname)
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            file_count = len([f for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f))])
            existing_dirs.append((dirname, file_count))
            print(f"  - {dirname} ({file_count} 个文件)")
    
    if not existing_dirs:
        print("  未检测到知识内容目录")
        return []
    
    print("\n请选择需要同步的知识内容目录：")
    selected = []
    for dirname, count in existing_dirs:
        if ask_yes_no(f"  同步 {dirname} ({count} 个文件)", False):
            selected.append(dirname)
    
    return selected

def generate_config(config_data):
    """生成配置文件"""
    config_content = '''#!/usr/bin/env python3
"""WorkBuddy Sync — 用户自定义配置

此文件由配置向导自动生成，请根据需要修改。
"""

import os

# ============================================================
# 路径配置
# ============================================================

# WorkBuddy 配置目录
WORKBUDDY_DIR = r"{workbuddy_dir}"

# IMA 配置目录
CONFIG_DIR = r"{ima_config_dir}"

# 工作空间目录
WORKSPACE_DIR = r"{workspace_dir}"

# ============================================================
# IMA API 配置
# ============================================================

# 同步笔记标题
SYNC_NOTE_TITLE = "{sync_note_title}"

# ============================================================
# 知识内容目录
# ============================================================

# 需要同步的知识内容子目录
KNOWLEDGE_SUBDIRS = {knowledge_subdirs}

# ============================================================
# 备份内容选择
# ============================================================

# 启用的备份类别
ENABLED_BACKUP_CATEGORIES = {enabled_categories}

# ============================================================
# 备份清理配置
# ============================================================

# 备份最大保留天数
MAX_BACKUP_AGE_DAYS = {max_backup_age_days}

# 最大备份数量
MAX_BACKUP_COUNT = {max_backup_count}

# ============================================================
# 文件瘦身配置
# ============================================================

# 每个技能最大文件数
MAX_FILES_PER_SKILL = {max_files_per_skill}

# 单个文件最大大小（字节）
MAX_FILE_SIZE = {max_file_size}

# ============================================================
# 槽位管理配置
# ============================================================

# 每个槽位最大快照数
MAX_SNAPSHOT_COUNT = {max_snapshot_count}

# ============================================================
# 微云配置（可选）
# ============================================================

# 启用微云备份
ENABLE_WEIYUN = {enable_weiyun}

# 微云连接器目录
WEIYUN_CONNECTOR_DIR = r"{weiyun_connector_dir}"

# 微云脚本目录
WEIYUN_SCRIPT_DIR = r"{weiyun_script_dir}"

# 微云目录 Key
WEIYUN_PDIR_KEY = "{weiyun_pdir_key}"

# 微云最大备份数
WEIYUN_MAX_BACKUPS = {weiyun_max_backups}

# ============================================================
# 子项目源代码配置（可选）
# ============================================================

# 子项目目录配置
PROJECT_SOURCE_DIRS = {{
    # 示例：
    # "daily-why": {{
    #     "path": os.path.join(WORKSPACE_DIR, "daily-why"),
    #     "patterns": ["*.py"],
    #     "extra_files": ["topics_context.json"],
    #     "description": "冷知识自动化流水线"
    # }},
}}
'''.format(
        workbuddy_dir=config_data['workbuddy_dir'].replace('\\', '\\\\'),
        ima_config_dir=config_data['ima_config_dir'].replace('\\', '\\\\'),
        workspace_dir=config_data['workspace_dir'].replace('\\', '\\\\'),
        sync_note_title=config_data.get('sync_note_title', 'WorkBuddy Sync Backup'),
        knowledge_subdirs=config_data.get('knowledge_subdirs', []),
        enabled_categories=config_data.get('enabled_categories', []),
        max_backup_age_days=config_data.get('max_backup_age_days', 90),
        max_backup_count=config_data.get('max_backup_count', 10),
        max_files_per_skill=config_data.get('max_files_per_skill', 15),
        max_file_size=config_data.get('max_file_size', 50 * 1024),
        max_snapshot_count=config_data.get('max_snapshot_count', 15),
        enable_weiyun='True' if config_data.get('enable_weiyun', False) else 'False',
        weiyun_connector_dir=config_data.get('weiyun_connector_dir', '').replace('\\', '\\\\'),
        weiyun_script_dir=config_data.get('weiyun_script_dir', '').replace('\\', '\\\\'),
        weiyun_pdir_key=config_data.get('weiyun_pdir_key', ''),
        weiyun_max_backups=config_data.get('weiyun_max_backups', 3),
    )
    
    return config_content

def main():
    """主函数"""
    print_banner()
    
    # 1. 检测 WorkBuddy 配置目录
    print("🔍 正在检测 WorkBuddy 配置目录...")
    detected_wb_dir = detect_workbuddy_dir()
    
    if detected_wb_dir:
        print(f"  ✅ 检测到: {detected_wb_dir}")
        wb_dir = detected_wb_dir
    else:
        print("  ⚠️  未自动检测到，请手动输入")
        wb_dir = get_user_input("请输入 WorkBuddy 配置目录路径")
    
    # 2. 检测工作空间目录
    print("\n🔍 正在检测工作空间目录...")
    detected_ws_dir = detect_workspace_dir()
    
    if detected_ws_dir:
        print(f"  ✅ 检测到: {detected_ws_dir}")
        ws_dir = detected_ws_dir
    else:
        print("  ⚠️  未自动检测到，请手动输入")
        ws_dir = get_user_input("请输入工作空间目录路径")
    
    # 3. 选择备份内容类别
    selected_categories = select_backup_categories()
    
    # 4. 选择知识内容子目录
    knowledge_subdirs = []
    if 'knowledge' in selected_categories:
        knowledge_subdirs = select_knowledge_subdirs(ws_dir)
    
    # 5. 微云配置
    enable_weiyun = False
    weiyun_config = {}
    if 'weiyun' in selected_categories:
        enable_weiyun = True
        print("\n☁️  微云配置：")
        print("  请确保已配置微云连接器。")
        weiyun_config['weiyun_connector_dir'] = get_user_input(
            "  微云连接器目录路径",
            default=os.path.join(wb_dir, "connectors", "your-connector-id")
        )
        weiyun_config['weiyun_script_dir'] = get_user_input(
            "  微云脚本目录路径",
            default=os.path.join(wb_dir, "connectors", "skills", "connector-tencent-weiyun", "scripts")
        )
        weiyun_config['weiyun_pdir_key'] = get_user_input("  微云目录 Key")
    
    # 6. 高级配置
    print("\n⚙️  高级配置（可选）：")
    if ask_yes_no("是否自定义高级配置", False):
        max_backup_age_days = int(get_user_input("  备份最大保留天数", default="90"))
        max_backup_count = int(get_user_input("  最大备份数量", default="10"))
        max_files_per_skill = int(get_user_input("  每个技能最大文件数", default="15"))
        max_snapshot_count = int(get_user_input("  每个槽位最大快照数", default="15"))
    else:
        max_backup_age_days = 90
        max_backup_count = 10
        max_files_per_skill = 15
        max_snapshot_count = 15
    
    # 7. 生成配置文件
    print("\n📝 正在生成配置文件...")
    
    config_data = {
        'workbuddy_dir': wb_dir,
        'ima_config_dir': os.path.join(os.path.expanduser("~"), ".config", "ima"),
        'workspace_dir': ws_dir,
        'sync_note_title': 'WorkBuddy Sync Backup',
        'knowledge_subdirs': knowledge_subdirs,
        'enabled_categories': selected_categories,
        'max_backup_age_days': max_backup_age_days,
        'max_backup_count': max_backup_count,
        'max_files_per_skill': max_files_per_skill,
        'max_file_size': 50 * 1024,
        'max_snapshot_count': max_snapshot_count,
        'enable_weiyun': enable_weiyun,
        **weiyun_config
    }
    
    config_content = generate_config(config_data)
    
    # 保存配置文件
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.user.py")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print(f"  ✅ 配置文件已保存到: {config_path}")
    
    # 8. 显示配置摘要
    print("\n" + "=" * 60)
    print("📋 配置摘要：")
    print("=" * 60)
    print(f"  WorkBuddy 目录: {wb_dir}")
    print(f"  工作空间目录: {ws_dir}")
    print(f"  备份类别: {', '.join(selected_categories)}")
    if knowledge_subdirs:
        print(f"  知识内容目录: {', '.join(knowledge_subdirs)}")
    if enable_weiyun:
        print(f"  微云备份: 已启用")
    print("=" * 60)
    
    # 9. 下一步操作提示
    print("\n🚀 下一步操作：")
    print("  1. 检查并修改 config.user.py 中的配置")
    print("  2. 配置 IMA API 凭证：")
    print(f"     mkdir -p {config_data['ima_config_dir']}")
    print(f"     echo 'your_client_id' > {os.path.join(config_data['ima_config_dir'], 'client_id')}")
    print(f"     echo 'your_api_key' > {os.path.join(config_data['ima_config_dir'], 'api_key')}")
    print("  3. 运行同步脚本：")
    print("     python sync_to_cloud.py")
    print("  4. 查看帮助：")
    print("     python sync_to_cloud.py --help")
    
    print("\n✨ 配置完成！祝您使用愉快！")

if __name__ == "__main__":
    main()
