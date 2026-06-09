#!/usr/bin/env python3
"""WorkBuddy Sync — 主同步脚本（通用版）

一键将 WorkBuddy 配置同步到腾讯 IMA 云端 + 微云网盘。

使用方式：
    python sync_to_cloud.py              # 默认同步
    python sync_to_cloud.py --dry-run    # 模拟运行
    python sync_to_cloud.py --health-check # 健康检查
    python sync_to_cloud.py --help       # 查看帮助
"""

import os
import sys
import argparse
from datetime import datetime

# Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入用户配置
try:
    from config.user import *
    print("[INFO] 使用用户自定义配置")
except ImportError:
    from config import *
    print("[INFO] 使用默认配置")

# 导入其他模块
from lib.ima_api import load_credentials, append_to_note
from lib.slot_manager import (
    get_today_slot, load_slot_mapping, save_slot_mapping,
    init_slots, ensure_slots_ready
)
from lib.collector import collect_sync_items, collect_special_items, collect_project_sources
from lib.stats import extract_stats
from lib.fingerprint import (
    compute_fingerprint, compute_light_fingerprint,
    load_previous_fingerprint, save_fingerprint,
    load_light_fingerprint, save_light_fingerprint,
)
from lib.cleaner import cleanup_old_backups
from lib.builder import (
    build_lightweight_snapshot, build_full_package,
    build_sync_package, build_note_content, build_note_content_v6
)
from lib.memory_manager import update_memory_md
from lib.weiyun import _upload_to_weiyun, _cleanup_local_packages
from lib.health import health_check


def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           WorkBuddy Sync v7.0 — 通用版                      ║
║                                                              ║
║  一键将 WorkBuddy 配置同步到腾讯 IMA 云端 + 微云网盘         ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_config_summary():
    """打印配置摘要"""
    print("📋 当前配置：")
    print(f"  WorkBuddy 目录: {WORKBUDDY_DIR}")
    print(f"  工作空间目录: {WORKSPACE_DIR}")
    print(f"  备份类别: {', '.join(ENABLED_BACKUP_CATEGORIES)}")
    if KNOWLEDGE_SUBDIRS:
        print(f"  知识内容目录: {', '.join(KNOWLEDGE_SUBDIRS)}")
    if ENABLE_WEIYUN:
        print(f"  微云备份: 已启用")
    print()


def run_default_mode(client_id, api_key, items, stats, args):
    """默认模式：单笔记覆盖（向后兼容 v3.1 行为）"""
    base64_content, package_size_kb, content_hash = build_sync_package(items, stats)

    print(f"[INFO] 数据包大小: {package_size_kb:.2f} KB")

    current_fingerprint = compute_fingerprint(items)
    previous = load_previous_fingerprint()

    if not args.force and previous and previous.get("fingerprint") == current_fingerprint:
        print("")
        print("=" * 48)
        print("[OK] 配置无变更，跳过上传")
        print(f"[INFO] 上次同步: {previous.get('timestamp', 'unknown')}")
        print("=" * 48)
        print("")
        update_memory_md("UNCHANGED", stats, package_size_kb)
        print("[SYNC_RESULT] UNCHANGED")
        print(f"[SYNC_STATS] skills={stats['skills']['count']} "
              f"workspaces={stats['workspaces']['count']} size={package_size_kb:.0f}KB")
        return

    if previous:
        print(f"[INFO] 检测到配置变更 (上次: {previous.get('timestamp', 'unknown')})")

    total_backups, deleted = cleanup_old_backups(client_id, api_key)
    note_content = build_note_content(base64_content, package_size_kb, content_hash,
                                      items, stats, mode="default")

    print("")
    print("[*] 正在上传到腾讯 IMA...")

    existing_note_id = None
    from lib.ima_api import find_existing_note
    existing_note_id = find_existing_note(client_id, api_key)
    if existing_note_id:
        print(f"[*] 找到已有笔记: {existing_note_id}，将更新内容")

    from lib.ima_api import upload_note, verify_upload
    success, result = upload_note(client_id, api_key, note_content)

    if not success:
        print(f"[ERROR] 上传失败: {result}")
        update_memory_md("FAILED", stats, package_size_kb)
        print("[SYNC_RESULT] FAILED")
        return

    print(f"[OK] 上传成功: {result}")

    if existing_note_id:
        verified = verify_upload(client_id, api_key, existing_note_id, content_hash)
        if verified:
            print("[OK] Hash 验证通过")
            update_memory_md("SUCCESS_VERIFIED", stats, package_size_kb)
            print("[SYNC_RESULT] SUCCESS_VERIFIED")
        else:
            print("[WARN] Hash 验证失败，但上传成功")
            update_memory_md("SUCCESS", stats, package_size_kb)
            print("[SYNC_RESULT] SUCCESS")
    else:
        update_memory_md("SUCCESS", stats, package_size_kb)
        print("[SYNC_RESULT] SUCCESS")

    print(f"[SYNC_STATS] skills={stats['skills']['count']} "
          f"workspaces={stats['workspaces']['count']} size={package_size_kb:.0f}KB")


def run_v6_mode(client_id, api_key, items, stats, args):
    """v6 模式：双备策略（IMA 轻量快照 + 微云完整包）"""
    print("[*] 使用 v6 双备策略...")

    # 1. 轻量指纹前置检测
    light_fingerprint = compute_light_fingerprint(items)
    previous_light = load_light_fingerprint()

    if not args.force and previous_light and previous_light.get("fingerprint") == light_fingerprint:
        print("")
        print("=" * 48)
        print("[OK] 文件系统无变更（轻量指纹匹配），跳过同步")
        print(f"[INFO] 上次同步: {previous_light.get('timestamp', 'unknown')}")
        print("=" * 48)
        print("")
        update_memory_md("UNCHANGED_LIGHT", stats, 0)
        print("[SYNC_RESULT] UNCHANGED_LIGHT")
        return

    # 2. 收集完整数据
    special_items = collect_special_items(items)
    project_items = collect_project_sources(items)
    all_items = items + special_items + project_items

    # 3. 构建轻量快照
    snapshot_data, snapshot_size_kb = build_lightweight_snapshot(all_items, stats)
    print(f"[INFO] 轻量快照大小: {snapshot_size_kb:.2f} KB")

    # 4. 检查是否超过 IMA 限制
    if snapshot_size_kb > 900:
        print(f"[WARN] 轻量快照超过 900KB，将使用完整包模式")
        # 回退到完整包模式
        base64_content, package_size_kb, content_hash = build_full_package(all_items, stats)
        note_content = build_note_content_v6(base64_content, package_size_kb, content_hash,
                                             all_items, stats, mode="full_package")
    else:
        # 使用轻量快照
        note_content = build_note_content_v6(snapshot_data, snapshot_size_kb, None,
                                             all_items, stats, mode="lightweight")

    # 5. 上传到 IMA
    print("")
    print("[*] 正在上传到腾讯 IMA...")

    slot = get_today_slot()
    slot_mapping = load_slot_mapping()
    note_id = slot_mapping.get(slot)

    if not note_id:
        print(f"[*] 槽位 {slot} 不存在，将创建新笔记")
        from lib.ima_api import create_note
        note_id = create_note(client_id, api_key, f"WB_{slot}")
        if note_id:
            slot_mapping[slot] = note_id
            save_slot_mapping(slot_mapping)
            print(f"[OK] 创建笔记成功: {note_id}")
        else:
            print("[ERROR] 创建笔记失败")
            update_memory_md("FAILED", stats, snapshot_size_kb)
            print("[SYNC_RESULT] FAILED")
            return

    # 追加到笔记
    from lib.ima_api import append_to_note
    success = append_to_note(client_id, api_key, note_id, note_content)

    if not success:
        print("[ERROR] 追加到笔记失败")
        update_memory_md("FAILED", stats, snapshot_size_kb)
        print("[SYNC_RESULT] FAILED")
        return

    print(f"[OK] 追加到笔记成功: {note_id}")

    # 6. 上传到微云（如果启用）
    weiyun_success = True
    if ENABLE_WEIYUN:
        print("")
        print("[*] 正在上传到微云...")
        try:
            # 构建完整包
            base64_content, package_size_kb, content_hash = build_full_package(all_items, stats)
            weiyun_success = _upload_to_weiyun(base64_content, package_size_kb)
            if weiyun_success:
                print("[OK] 微云上传成功")
            else:
                print("[WARN] 微云上传失败")
        except Exception as e:
            print(f"[WARN] 微云上传异常: {e}")
            weiyun_success = False

    # 7. 保存指纹
    save_light_fingerprint(light_fingerprint)
    save_fingerprint(compute_fingerprint(all_items))

    # 8. 清理本地包
    _cleanup_local_packages()

    # 9. 更新状态
    if weiyun_success:
        update_memory_md("SUCCESS", stats, snapshot_size_kb)
        print("[SYNC_RESULT] SUCCESS")
    else:
        update_memory_md("PARTIAL", stats, snapshot_size_kb)
        print("[SYNC_RESULT] PARTIAL")

    print(f"[SYNC_STATS] skills={stats['skills']['count']} "
          f"workspaces={stats['workspaces']['count']} size={snapshot_size_kb:.0f}KB")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="WorkBuddy Sync — 跨设备配置同步工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python sync_to_cloud.py              # 默认同步
  python sync_to_cloud.py --dry-run    # 模拟运行
  python sync_to_cloud.py --health-check # 健康检查
  python sync_to_cloud.py --force      # 强制同步
  python sync_to_cloud.py --default    # 使用旧版单笔记模式
        """
    )

    parser.add_argument("--dry-run", action="store_true",
                        help="模拟运行，不实际上传")
    parser.add_argument("--health-check", action="store_true",
                        help="健康检查，检测备份覆盖范围完整性")
    parser.add_argument("--force", action="store_true",
                        help="强制同步，跳过变更检测")
    parser.add_argument("--default", action="store_true",
                        help="使用旧版单笔记模式（向后兼容）")
    parser.add_argument("--init-slot", action="store_true",
                        help="初始化槽位映射")
    parser.add_argument("--reset", action="store_true",
                        help="重置今天槽位计数器")

    args = parser.parse_args()

    print_banner()
    print_config_summary()

    # 健康检查模式
    if args.health_check:
        print("[*] 运行健康检查...")
        health_check()
        return

    # 初始化槽位
    if args.init_slot:
        print("[*] 初始化槽位映射...")
        init_slots()
        return

    # 重置槽位
    if args.reset:
        print("[*] 重置今天槽位计数器...")
        slot = get_today_slot()
        slot_mapping = load_slot_mapping()
        if slot in slot_mapping:
            del slot_mapping[slot]
            save_slot_mapping(slot_mapping)
            print(f"[OK] 已重置槽位: {slot}")
        else:
            print(f"[INFO] 槽位 {slot} 不存在，无需重置")
        return

    # 加载 IMA 凭证
    client_id, api_key = load_credentials()
    if not client_id or not api_key:
        print("[ERROR] 未找到 IMA 凭证，请先配置：")
        print(f"  mkdir -p {CONFIG_DIR}")
        print(f"  echo 'your_client_id' > {os.path.join(CONFIG_DIR, 'client_id')}")
        print(f"  echo 'your_api_key' > {os.path.join(CONFIG_DIR, 'api_key')}")
        print("")
        print("凭证获取地址：https://ima.qq.com/agent-interface")
        return

    # 收集数据
    print("[*] 开始收集配置数据...")
    items = collect_sync_items()

    if not items:
        print("[WARN] 未收集到任何数据")
        update_memory_md("NO_DATA", {}, 0)
        print("[SYNC_RESULT] NO_DATA")
        return

    # 提取统计信息
    stats = extract_stats(items)
    print(f"[INFO] 收集完成: {stats['skills']['count']} 个技能, "
          f"{stats['workspaces']['count']} 个工作空间")

    # 模拟运行模式
    if args.dry_run:
        print("")
        print("=" * 48)
        print("[DRY RUN] 模拟运行完成，未实际上传")
        print("=" * 48)
        print("")
        print("将要同步的内容：")
        for item in items:
            print(f"  - {item.get('path', item.get('type', 'unknown'))}")
        print("")
        print(f"总计: {len(items)} 个项目")
        return

    # 确保槽位就绪
    ensure_slots_ready(client_id, api_key)

    # 执行同步
    if args.default:
        run_default_mode(client_id, api_key, items, stats, args)
    else:
        run_v6_mode(client_id, api_key, items, stats, args)


if __name__ == "__main__":
    main()
