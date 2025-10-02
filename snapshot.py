#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
from datetime import datetime

# ==============================================================================
# 1. 組態設定 (Configuration)
# ==============================================================================

# -- 排除清單 --
# 在此處新增您想忽略的目錄或檔案名稱。
# 這會進行部分匹配，例如 "node_modules" 會排除所有路徑中包含此名稱的項目。
EXCLUDES = [
    "node_modules",
    "dist",
    ".git",
    ".vscode",
    "__pycache__",
    "snapshot.py",  # 忽略本腳本自己
    "snapshot.md",  # 忽略輸出的 Markdown 檔案
    "venv",  
    ".venv", 
]

# -- 檔案掃描目標 --
# 定義要掃描的副檔名。
TARGET_EXTENSIONS = ['.py', '.js', '.ts', '.vue']

# -- 目錄樹設定 --
# 設定目錄樹顯示的最大深度。
MAX_TREE_DEPTH = 5

# -- 輸出檔案名稱 --
OUTPUT_FILENAME = "snapshot.md"


# ==============================================================================
# 2. 檔案與目錄掃描 (File & Directory Scanning)
# ==============================================================================

def should_exclude(path, is_dir=False):
    """檢查給定的路徑是否應被排除。"""
    parts = path.split(os.sep)
    # 對於目錄，我們檢查它自身是否在排除清單中
    if is_dir:
        return any(excluded in parts[-1] for excluded in EXCLUDES)
    # 對於檔案，檢查路徑的任何部分是否匹配
    return any(excluded in part for part in parts for excluded in EXCLUDES)

def get_project_files(root_dir):
    """
    遞迴掃描專案目錄，找出所有符合條件的檔案。
    """
    matched_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # 過濾要排除的目錄
        dirnames[:] = [d for d in dirnames if not should_exclude(os.path.join(dirpath, d), is_dir=True)]

        for filename in filenames:
            if not should_exclude(os.path.join(dirpath, filename)):
                if any(filename.endswith(ext) for ext in TARGET_EXTENSIONS):
                    matched_files.append(os.path.join(dirpath, filename))
    return matched_files


# ==============================================================================
# 3. 程式碼解析 (Code Parsing)
# ==============================================================================

def parse_code_functions(file_path):
    """
    解析單一檔案，根據不同模式擷取函式與註解。
    - Python: `def function_name(...):`
    - JS/TS: `export function ...`, `export const useXxx = ...`
    """
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return [] # 無法讀取檔案時返回空列表

    # 正則表達式 (可在此處自訂)
    # 匹配 Python 的函式、JS/TS 的 export function/const
    patterns = [
        re.compile(r"^\s*#\s*(.*)"),  # 註解: # comment
        re.compile(r"^\s*//\s*(.*)"), # 註解: // comment
        re.compile(r"^\s*def\s+([a-zA-Z0-9_]+\(.*\)):"), # Python: def my_func(...):
        re.compile(r"^\s*async\s+def\s+([a-zA-Z0-9_]+\(.*\)):"), # Python: async def my_func(...):
        re.compile(r"^\s*export\s+(?:async\s+)?function\s+([a-zA-Z0-9_]+\(.*\))"), # JS/TS: export function myFunc(...)
        re.compile(r"^\s*export\s+const\s+([a-zA-Z0-9_]+\s*=\s*\(.*\)\s*=>)"), # JS/TS: export const myArrowFunc = (...) =>
        re.compile(r"^\s*export\s+const\s+(use[A-Z][a-zA-Z0-9_]+)\s*="), # JS/TS Vue composable: export const useMyComposable =
    ]

    last_comment = ""
    for line in lines:
        is_function_line = False
        # 檢查是否為註解
        comment_match_py = patterns[0].match(line)
        comment_match_js = patterns[1].match(line)

        if comment_match_py:
            last_comment = comment_match_py.group(1).strip()
            continue
        if comment_match_js:
            last_comment = comment_match_js.group(1).strip()
            continue

        # 檢查是否為函式定義
        for pattern in patterns[2:]:
            match = pattern.match(line)
            if match:
                signature = match.group(1).strip()
                functions.append({
                    "comment": last_comment,
                    "signature": signature
                })
                is_function_line = True
                break
        
        # 如果這行不是函式也不是註解，就重置 last_comment
        if not is_function_line:
            last_comment = ""
            
    return functions


# ==============================================================================
# 4. 目錄樹生成 (Directory Tree Generation)
# ==============================================================================

def generate_directory_tree(root_dir):
    """
    生成專案的 ASCII 目錄樹。
    """
    tree = []
    root_level = root_dir.count(os.sep)

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # 過濾排除的目錄
        dirnames[:] = [d for d in dirnames if not should_exclude(os.path.join(dirpath, d), is_dir=True)]
        
        level = dirpath.count(os.sep) - root_level
        if level >= MAX_TREE_DEPTH:
            dirnames[:] = [] # 不再深入
            continue

        indent = '│   ' * (level) + '├── '
        sub_indent = '│   ' * (level + 1) + '├── '
        
        # 處理目錄結構
        dir_name = os.path.basename(dirpath)
        if level == 0:
            tree.append(f"{dir_name}/")
        else:
            parent_path = os.path.dirname(dirpath)
            parent_dirs = os.listdir(parent_path)
            # 檢查是否為同層的最後一個目錄，以決定樹狀圖的符號
            if dir_name == [d for d in parent_dirs if os.path.isdir(os.path.join(parent_path, d)) and not should_exclude(os.path.join(parent_path, d), is_dir=True)][-1]:
                indent = '│   ' * (level-1) + '└── '
                sub_indent = '    ' + '│   ' * level + '├── '

            tree.append(f"{indent}{dir_name}/")

        # 處理檔案
        if level + 1 < MAX_TREE_DEPTH:
            filtered_files = [f for f in filenames if not should_exclude(os.path.join(dirpath, f))]
            for i, filename in enumerate(sorted(filtered_files)):
                connector = '└── ' if i == len(filtered_files) - 1 else '├── '
                tree.append(f"{'│   ' * (level)}{'    ' if '└──' in indent else ''}{connector}{filename}")
                
    return "\n".join(tree)


# ==============================================================================
# 5. 依賴收集 (Dependency Collection)
# ==============================================================================

def find_and_parse_dependencies(root_dir):
    """
    尋找所有 package.json 並解析其依賴。
    (此處以 package.json 為例，可擴充支援 requirements.txt 或 pyproject.toml)
    """
    dependencies_map = {}
    for dirpath, _, filenames in os.walk(root_dir):
        if should_exclude(dirpath, is_dir=True):
            continue
            
        if "package.json" in filenames:
            filepath = os.path.join(dirpath, "package.json")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    project_name = data.get("name", os.path.basename(dirpath))
                    
                    dependencies_map[project_name] = {
                        "dependencies": data.get("dependencies", {}),
                        "devDependencies": data.get("devDependencies", {}),
                    }
            except Exception as e:
                print(f"Warning: Could not parse {filepath}: {e}")

    return dependencies_map


# ==============================================================================
# 6. Markdown 輸出 (Markdown Output)
# ==============================================================================

def generate_markdown(project_name, tree, functions_by_file, dependencies):
    """
    將所有收集到的資訊組合成 Markdown 格式。
    """
    md_content = [
        f"# {project_name} 專案快照",
        f"> 自動生成於: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "## 專案目錄結構",
        "```",
        tree,
        "```\n",
        "## 函式清單",
    ]

    for file_path, functions in functions_by_file.items():
        if not functions:
            continue
        
        relative_path = os.path.relpath(file_path, start=os.getcwd())
        md_content.append(f"### `{relative_path}`")
        md_content.append("```")
        for func in functions:
            if func["comment"]:
                md_content.append(f"// {func['comment']}")
            md_content.append(func["signature"])
        md_content.append("```")

    md_content.append("\n## 依賴清單")

    if not dependencies:
        md_content.append("未在本專案中找到 `package.json` 檔案。")
    else:
        for name, deps in dependencies.items():
            md_content.append(f"### 專案: {name}")
            if deps["dependencies"]:
                md_content.append("#### dependencies")
                md_content.append("```json")
                md_content.append(json.dumps(deps["dependencies"], indent=2))
                md_content.append("```")
            if deps["devDependencies"]:
                md_content.append("#### devDependencies")
                md_content.append("```json")
                md_content.append(json.dumps(deps["devDependencies"], indent=2))
                md_content.append("```")

    return "\n".join(md_content)

# ==============================================================================
# 7. 主執行函式 (Main Execution)
# ==============================================================================

def main():
    """
    主執行函式。
    """
    project_root = os.getcwd()
    project_name = os.path.basename(project_root)

    print(f"[*] 正在為 '{project_name}' 專案生成快照...")

    # 1. 產生目錄樹
    print("[1/4] 正在生成目錄結構樹...")
    directory_tree = generate_directory_tree(project_root)

    # 2. 掃描並解析檔案
    print("[2/4] 正在掃描並解析程式碼檔案...")
    project_files = get_project_files(project_root)
    functions_by_file = {
        file: parse_code_functions(file) for file in project_files
    }
    
    # 3. 收集依賴
    print("[3/4] 正在收集專案依賴...")
    dependencies = find_and_parse_dependencies(project_root)

    # 4. 生成並寫入 Markdown
    print(f"[4/4] 正在將結果寫入 '{OUTPUT_FILENAME}'...")
    markdown_output = generate_markdown(project_name, directory_tree, functions_by_file, dependencies)
    
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    
    print(f"\n[+] 快照成功生成！請查看 ./{OUTPUT_FILENAME}")


if __name__ == "__main__":
    main()