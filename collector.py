#!/usr/bin/env python3
"""WorkBuddy Sync — 数据收集层（通用版）

支持用户自定义备份类别。
"""

import os
import json
import glob
import hashlib
import base64
import gzip
from datetime import datetime

# 尝试导入用户配置，否则使用默认配置
try:
    from config.user import *
except ImportError:
    from config import *


def should_exclude_dir(dir_name):
    """判断是否应排除该子目录"""
    return dir_name.lower() in EXCLUDED_SUBDIRS


def file_hash(filepath):
    """计算文件内容哈希"""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files_recursive(base_path, display_name, max_files=None, max_file_size=None):
    """递归收集文件（排除指定子目录），只取文本文件"""
    all_files = []
    skipped_large = []

    for root, dirs, filenames in os.walk(base_path):
        dirs[:] = [d for d in dirs if not should_exclude_dir(d)]

        for filename in filenames:
            filepath = os.path.join(root, filename)
            if not os.path.isfile(filepath):
                continue

            fsize = os.path.getsize(filepath)

            if max_file_size and fsize > max_file_size:
                skipped_large.append(os.path.relpath(filepath, base_path).replace(os.sep, "/"))
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                all_files.append({
                    "name": os.path.relpath(filepath, base_path).replace(os.sep, "/"),
                    "content": content,
                    "_size": fsize
                })
            except Exception:
                pass

    if max_files and len(all_files) > max_files:
        all_files.sort(key=lambda x: -x["_size"])
        truncated = len(all_files) - max_files
        kept = all_files[:max_files]
        if truncated > 0:
            print(f"       [~] 截断 {truncated} 个文件（保留最大的 {max_files} 个）")
        all_files = kept

    if skipped_large:
        print(f"       [~] 跳过 {len(skipped_large)} 个大文件（>{max_file_size // 1024}KB）")

    for f in all_files:
        f.pop("_size", None)

    return all_files


def collect_plugins_config():
    """收集 plugins 目录的顶级配置文件（排除所有子目录的内容）"""
    items = []
    plugins_path = os.path.join(WORKBUDDY_DIR, "plugins")
    if not os.path.exists(plugins_path):
        return items

    data = []
    for item in sorted(os.listdir(plugins_path)):
        item_path = os.path.join(plugins_path, item)
        if os.path.isfile(item_path):
            try:
                with open(item_path, "r", encoding="utf-8") as f:
                    content = f.read()
                fsize = os.path.getsize(item_path)
                if fsize > MAX_FILE_SIZE:
                    print(f"  [~] 跳过 plugins/{item} ({fsize/1024:.1f}KB, 超限)")
                    continue
                data.append({"name": item, "content": content})
                print(f"  [+] 插件配置: {item}")
            except Exception:
                pass
        elif os.path.isdir(item_path):
            print(f"  [~] 跳过 plugins/{item}/ (目录)")

    if data:
        items.append({"type": "plugins", "path": "plugins", "data": data})
    return items


def collect_directory_items(dir_name, exclude_dirs=None):
    """收集指定目录下的配置项"""
    items = []
    dir_path = os.path.join(WORKBUDDY_DIR, dir_name)
    if not os.path.exists(dir_path):
        return items

    exclude_dirs = exclude_dirs or set()
    data = []

    for item in sorted(os.listdir(dir_path)):
        if item in exclude_dirs:
            continue
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path):
            try:
                with open(item_path, "r", encoding="utf-8") as f:
                    data.append({"name": item, "content": f.read()})
                print(f"  [+] {dir_name}/{item}")
            except Exception:
                pass
        elif os.path.isdir(item_path):
            files = collect_files_recursive(item_path, item)
            if files:
                data.append({"name": item, "type": "directory", "files": files})
                print(f"  [+] {dir_name}/{item}/")

    if data:
        items.append({"type": "directory", "path": dir_name, "data": data})
    return items


def collect_workspace_items():
    """收集工作空间的记忆和知识内容"""
    items = []

    if not os.path.exists(WORKSPACE_DIR):
        print("[~] 未找到工作空间目录，跳过工作空间记忆同步")
        return items

    print("[*] 开始收集工作空间记忆和知识内容...")

    # A. 工作空间 .workbuddy/memory（如果启用）
    if 'memory' in ENABLED_BACKUP_CATEGORIES:
        if os.path.exists(WORKSPACE_MEMORY_DIR):
            mem_files = []
            for fn in sorted(os.listdir(WORKSPACE_MEMORY_DIR)):
                fp = os.path.join(WORKSPACE_MEMORY_DIR, fn)
                if os.path.isfile(fp) and fn.endswith(".md"):
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            content = f.read()
                        fsize = os.path.getsize(fp)
                        if fsize > MAX_FILE_SIZE:
                            print(f"  [~] 跳过 ws-memory/{fn} ({fsize/1024:.1f}KB, 超限)")
                            continue
                        mem_files.append({
                            "name": fn,
                            "content": content,
                            "modified": datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
                            "hash": file_hash(fp)
                        })
                        print(f"  [+] ws-memory: {fn}")
                    except Exception as e:
                        print(f"  [!] 跳过 ws-memory/{fn}: {e}")
            if mem_files:
                items.append({
                    "type": "directory",
                    "path": "workspace/memory",
                    "data": mem_files,
                    "_meta": {"count": len(mem_files)}
                })

    # B. 工作空间 automations（如果启用）
    if 'automations' in ENABLED_BACKUP_CATEGORIES:
        if os.path.exists(WORKSPACE_AUTOMATIONS_DIR):
            auto_dirs = []
            for auto_id in sorted(os.listdir(WORKSPACE_AUTOMATIONS_DIR)):
                auto_path = os.path.join(WORKSPACE_AUTOMATIONS_DIR, auto_id)
                if os.path.isdir(auto_path):
                    files = collect_files_recursive(auto_path, f"ws-auto-{auto_id}")
                    if files:
                        auto_dirs.append({"id": f"ws-{auto_id}", "files": files})
                        print(f"  [+] ws-automation: {auto_id} ({len(files)} 文件)")
            if auto_dirs:
                items.append({
                    "type": "directory",
                    "path": "workspace/automations",
                    "data": auto_dirs,
                    "_meta": {"count": len(auto_dirs)}
                })

    # C. 知识内容目录（如果启用）
    if 'knowledge' in ENABLED_BACKUP_CATEGORIES:
        for subdir in KNOWLEDGE_SUBDIRS:
            subdir_full = os.path.join(WORKSPACE_DIR, subdir)
            if os.path.exists(subdir_full):
                knowledge_files = []
                for root, dirs, filenames in os.walk(subdir_full):
                    rel_depth = root[len(subdir_full):].count(os.sep)
                    if rel_depth > 1:
                        dirs[:] = []
                        continue
                    dirs[:] = [d for d in dirs if not should_exclude_dir(d)]
                    for fn in sorted(filenames):
                        fp = os.path.join(root, fn)
                        if not os.path.isfile(fp):
                            continue
                        if not fn.endswith((".md", ".txt")):
                            continue
                        fsize = os.path.getsize(fp)
                        if fsize > MAX_FILE_SIZE:
                            continue
                        try:
                            with open(fp, "r", encoding="utf-8") as f:
                                content = f.read()
                            knowledge_files.append({
                                "name": os.path.relpath(fp, subdir_full).replace(os.sep, "/"),
                                "content": content,
                                "_hash": file_hash(fp)
                            })
                        except Exception:
                            pass

                if knowledge_files:
                    items.append({
                        "type": "directory",
                        "path": f"workspace/{subdir}",
                        "data": knowledge_files,
                        "_meta": {"count": len(knowledge_files)}
                    })
                    print(f"  [+] 知识库: {subdir} ({len(knowledge_files)} 个文件)")

    return items


def collect_special_items(existing_items=None):
    """收集特殊项目（workbuddy.db, connectors, IMA凭证）"""
    items = []

    existing_size_kb = 0
    if existing_items:
        existing_json_kb = len(json.dumps(existing_items, ensure_ascii=False)) / 1024
    else:
        existing_json_kb = 0

    ESTIMATED_APPEND_LIMIT_KB = 8500

    # --- workbuddy.db（如果启用）
    if 'workbuddy_db' in ENABLED_BACKUP_CATEGORIES:
        wbdb_path = os.path.join(WORKBUDDY_DIR, "workbuddy.db")
        if os.path.exists(wbdb_path):
            raw_size = os.path.getsize(wbdb_path)
            if raw_size <= MAX_BINARY_FILE_SIZE:
                try:
                    with open(wbdb_path, "rb") as f:
                        raw_data = f.read()
                    compressed = gzip.compress(raw_data)
                    b64_data = base64.b64encode(compressed).decode("ascii")
                    b64_size_kb = len(b64_data) / 1024
                    estimated_total = (existing_json_kb + b64_size_kb) * 1.37 + 50
                    if estimated_total > ESTIMATED_APPEND_LIMIT_KB:
                        print(f"  [~] workbuddy.db 跳过（{estimated_total:.0f}KB → 超 {ESTIMATED_APPEND_LIMIT_KB}KB 上限）")
                        print(f"      DB 体积过大，不适合每日增量同步（IMA 约 5MB 上限）")
                        print(f"      建议：slot 重置时或独立备份包含")
                    else:
                        items.append({
                            "type": "binary_file",
                            "path": "workbuddy.db",
                            "content": b64_data,
                            "encoding": "gzip+base64",
                            "raw_size": raw_size,
                            "compressed_size": len(compressed),
                            "_meta": {"warning": "自动化引擎数据库 — 所有调度定义"}
                        })
                        print(f"  [+] workbuddy.db ({raw_size/1024/1024:.1f}MB → {len(compressed)/1024/1024:.1f}MB gzip)")
                except Exception as e:
                    print(f"  [~] workbuddy.db 压缩失败: {e}")
            else:
                print(f"  [~] workbuddy.db ({raw_size/1024:.0f}KB 超上限 {MAX_BINARY_FILE_SIZE/1024/1024:.0f}MB)")

    # --- connectors/（如果启用）
    if 'connectors' in ENABLED_BACKUP_CATEGORIES:
        connectors_path = os.path.join(WORKBUDDY_DIR, "connectors")
        if os.path.exists(connectors_path):
            connector_items = []
            for root, dirs, files in os.walk(connectors_path):
                for fn in sorted(files):
                    fp = os.path.join(root, fn)
                    try:
                        fsize = os.path.getsize(fp)
                        if fsize > MAX_FILE_SIZE:
                            print(f"       [~] 跳过 connectors 文件: {fn} ({fsize/1024:.0f}KB, 超限)")
                            continue
                        rel_path = os.path.relpath(fp, connectors_path)
                        with open(fp, "r", encoding="utf-8") as f:
                            content = f.read()
                        connector_items.append({
                            "name": rel_path,
                            "content": content,
                            "size": fsize
                        })
                    except (UnicodeDecodeError, IOError):
                        try:
                            with open(fp, "rb") as f:
                                b64 = base64.b64encode(f.read()).decode("ascii")
                            connector_items.append({
                                "name": os.path.relpath(fp, connectors_path),
                                "content": f"[base64]{b64}",
                                "size": fsize,
                                "encoding": "base64"
                            })
                        except Exception:
                            pass
            if connector_items:
                items.append({
                    "type": "directory",
                    "path": "connectors",
                    "data": connector_items,
                    "_meta": {"count": len(connector_items)}
                })
                print(f"  [+] connectors/ ({len(connector_items)} 个文件)")

    # --- IMA 凭证（如果启用）
    if 'ima_creds' in ENABLED_BACKUP_CATEGORIES:
        creds_dir = os.path.expanduser("~/.config/ima")
        if os.path.exists(creds_dir):
            cred_files = []
            for cred_fn in ["client_id", "api_key"]:
                cred_fp = os.path.join(creds_dir, cred_fn)
                if os.path.exists(cred_fp):
                    with open(cred_fp, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    cred_files.append({"name": cred_fn, "content": content})
            if cred_files:
                items.append({
                    "type": "credentials",
                    "path": ".config/ima",
                    "data": cred_files,
                    "_meta": {"count": len(cred_files), "warning": "IMA 凭证 — 新机还原必需"}
                })
                print(f"  [+] IMA 凭证 ({len(cred_files)} 个文件) — 解决鸡生蛋问题")

    return items


def collect_project_sources(existing_items=None):
    """收集子项目源代码文件"""
    items = []

    if not os.path.exists(WORKSPACE_DIR):
        return items

    existing_json_kb = 0
    if existing_items:
        existing_json_kb = len(json.dumps(existing_items, ensure_ascii=False)) / 1024
    EST_BASE64_OVERHEAD = 1.37

    print("[*] 开始收集子项目源代码...")

    for key, cfg in PROJECT_SOURCE_DIRS.items():
        project_dir = cfg["path"]
        if not os.path.exists(project_dir):
            continue

        project_files = []
        collected_paths = set()
        for pattern in cfg["patterns"]:
            for fp in glob.glob(os.path.join(project_dir, pattern), recursive=False):
                if os.path.isfile(fp):
                    collected_paths.add(fp)

        for extra in cfg["extra_files"]:
            fp = os.path.join(project_dir, extra)
            if os.path.isfile(fp):
                collected_paths.add(fp)

        for fp in sorted(collected_paths):
            fname = os.path.basename(fp)
            fsize = os.path.getsize(fp)
            try:
                if fsize <= MAX_FILE_SIZE:
                    with open(fp, "r", encoding="utf-8") as f:
                        content = f.read()
                    project_files.append({
                        "name": f"{key}/{fname}",
                        "content": content,
                        "size": fsize,
                    })
                    print(f"  [+] 项目源: {key}/{fname} ({fsize/1024:.1f}KB)")
                elif fsize <= MAX_BINARY_FILE_SIZE:
                    with open(fp, "rb") as f:
                        raw_data = f.read()
                    compressed = gzip.compress(raw_data)
                    b64_data = base64.b64encode(compressed).decode("ascii")
                    b64_size_kb = len(b64_data) / 1024

                    est_total = (existing_json_kb + b64_size_kb) * EST_BASE64_OVERHEAD
                    if est_total > 8500:
                        print(f"  [~] 项目源: {key}/{fname} 跳过（{b64_size_kb:.0f}KB → 超上限）")
                        continue

                    project_files.append({
                        "name": f"{key}/{fname}",
                        "content": b64_data,
                        "encoding": "gzip+base64",
                        "size": fsize,
                        "compressed_size": len(compressed),
                    })
                    print(f"  [+] 项目源: {key}/{fname} ({fsize/1024:.0f}KB → {len(compressed)/1024:.0f}KB gzip)")
                else:
                    print(f"  [~] 项目源: {key}/{fname} 跳过（{fsize/1024:.0f}KB 超限）")
            except Exception as e:
                print(f"  [~] 项目源: {key}/{fname} 跳过: {e}")

        if project_files:
            items.append({
                "type": "directory",
                "path": f"project_sources/{key}",
                "data": project_files,
                "_meta": {"count": len(project_files), "description": cfg["description"]}
            })

    return items


def collect_sync_items():
    """收集要同步的内容（瘦身版）"""
    items = []

    if not os.path.exists(WORKBUDDY_DIR):
        print(f"[错误] 未找到 WorkBuddy 配置目录 ({WORKBUDDY_DIR})")
        return items

    print("[*] 开始收集 WorkBuddy 配置...")

    # 1. 核心配置文件（如果启用）
    if 'core' in ENABLED_BACKUP_CATEGORIES:
        core_files = BACKUP_CORE_FILES

        for filename in core_files:
            filepath = os.path.join(WORKBUDDY_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                items.append({
                    "type": "file",
                    "path": filename,
                    "content": content,
                    "size": os.path.getsize(filepath),
                    "hash": file_hash(filepath)
                })
                print(f"  [+] {filename}")

    # 2. Plugins 配置（如果启用 skills）
    if 'skills' in ENABLED_BACKUP_CATEGORIES:
        items.extend(collect_plugins_config())

    # 3. Skills Marketplace — 跳过
    sm_path = os.path.join(WORKBUDDY_DIR, "skills-marketplace")
    if os.path.exists(sm_path):
        print("  [~] 跳过 skills-marketplace（marketplace 缓存，自动恢复）")

    # 4. Skills 目录（如果启用）
    if 'skills' in ENABLED_BACKUP_CATEGORIES:
        skills_path = os.path.join(WORKBUDDY_DIR, "skills")
        if os.path.exists(skills_path):
            skills_data = []
            skill_names = []
            for skill_dir in sorted(os.listdir(skills_path)):
                skill_full_path = os.path.join(skills_path, skill_dir)
                if os.path.isdir(skill_full_path):
                    files = collect_files_recursive(
                        skill_full_path, skill_dir,
                        max_files=MAX_FILES_PER_SKILL,
                        max_file_size=MAX_FILE_SIZE
                    )
                    if files:
                        skills_data.append({"name": skill_dir, "files": files})
                        skill_names.append(skill_dir)
                        print(f"  [+] 技能: {skill_dir} ({len(files)}个核心文件)")
            if skills_data:
                items.append({
                    "type": "directory",
                    "path": "skills",
                    "data": skills_data,
                    "_meta": {"count": len(skills_data), "names": skill_names}
                })

    # 5. Memory 目录（如果启用）
    if 'memory' in ENABLED_BACKUP_CATEGORIES:
        memory_path = os.path.join(WORKBUDDY_DIR, "memory")
        if os.path.exists(memory_path):
            memory_files = []
            for filename in sorted(os.listdir(memory_path)):
                filepath = os.path.join(memory_path, filename)
                if os.path.isfile(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    memory_files.append({
                        "name": filename,
                        "content": content,
                        "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                        "hash": file_hash(filepath)
                    })
                    print(f"  [+] 记忆: {filename}")
            if memory_files:
                items.append({
                    "type": "directory",
                    "path": "memory",
                    "data": memory_files,
                    "_meta": {"count": len(memory_files)}
                })

    # 6. Automations 目录（如果启用）
    if 'automations' in ENABLED_BACKUP_CATEGORIES:
        automations_path = os.path.join(WORKBUDDY_DIR, "automations")
        if os.path.exists(automations_path):
            automation_dirs = []
            for auto_id in sorted(os.listdir(automations_path)):
                auto_full_path = os.path.join(automations_path, auto_id)
                if os.path.isdir(auto_full_path):
                    files = collect_files_recursive(auto_full_path, auto_id)
                    if files:
                        automation_dirs.append({"id": auto_id, "files": files})
                        print(f"  [+] 自动化: {auto_id}")
            if automation_dirs:
                items.append({
                    "type": "directory",
                    "path": "automations",
                    "data": automation_dirs,
                    "_meta": {"count": len(automation_dirs)}
                })

    # 7. 工作空间配置（如果启用）
    if 'workspace' in ENABLED_BACKUP_CATEGORIES:
        workspace_files = []
        if os.path.exists(WORKBUDDY_APP_DATA):
            for workspace_id in sorted(os.listdir(WORKBUDDY_APP_DATA)):
                ws_json_path = os.path.join(WORKBUDDY_APP_DATA, workspace_id, "workspace.json")
                if os.path.exists(ws_json_path):
                    with open(ws_json_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    try:
                        ws_data = json.loads(content)
                        workspace_folder = ws_data.get("folder", "")
                    except Exception:
                        workspace_folder = ""
                    workspace_files.append({
                        "workspace_id": workspace_id,
                        "folder": workspace_folder,
                        "content": content,
                        "hash": file_hash(ws_json_path)
                    })
                    print(f"  [+] 工作空间: {workspace_id}")

        if workspace_files:
            items.append({
                "type": "workspace_config",
                "path": "workspace.json",
                "data": workspace_files,
                "_meta": {"count": len(workspace_files)}
            })

    # 8. 工作空间记忆和知识内容
    items.extend(collect_workspace_items())

    return items
