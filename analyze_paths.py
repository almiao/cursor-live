#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析history.entries中文件路径的最长公共路径
"""

import os
import urllib.parse

def analyze_history_entries():
    """
    分析用户提供的history.entries数据，计算最长公共路径
    """
    # 用户提供的history.entries数据
    entries = [
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/views/KnowledgeMigration.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/data/releaseNotes.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/ReviewComment.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/services/FeishuService.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/public/knowledge-base-fetcher/background.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/public/knowledge-base-fetcher/content.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/public/doc.html"}},
        {"editor":{"resource":"file:///Applications/Cursor.app/Contents/Resources/app/extensions/node_modules/typescript/lib/lib.dom.d.ts"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/.trae/rules/project_rules.md"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/public/extensions/knowledge-base-fetcher/background.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/public/extensions/knowledge-base-fetcher/popup.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/views/GrayRelease.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/extensions/knowledge-base-fetcher/manifest.json"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/DiffSourceForm.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/DiffView.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/DiffViewDemo.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/DevelopmentPipeline.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/views/HomePage.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/router/index.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/views/Home.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/views/CodeReview.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/DiffViewer.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/App.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/main.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/HelloWorld.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/README.md"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/node_modules/vue/types/v3-component-options.d.ts"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/DefaultAvatar.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/services/AIReviewService.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/public/index.html"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/components/GitLabConfig.vue"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/src/store/index.js"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/.gitignore"}},
        {"editor":{"resource":"file:///Users/dxm/IdeaProjects/dxm/fscene/codereview-fe/extensions/knowledge-base-fetcher/background.js"}}
    ]
    
    print("=== 分析history.entries中的文件路径 ===")
    print(f"总共有 {len(entries)} 个条目")
    print()
    
    # 提取文件路径
    paths = []
    for i, entry in enumerate(entries):
        resource = entry.get("editor", {}).get("resource", "")
        if resource and resource.startswith("file:///"):
            # 方法1: 直接截取 (可能丢失开头斜杠)
            path1 = resource[len("file:///"):]
            
            # 方法2: 使用pathlib和urllib.parse (更健壮)
            from pathlib import Path
            path2 = Path(urllib.parse.unquote(resource[len("file:///"):])).as_posix()
            
            paths.append(path2)  # 使用更健壮的方法
            
            if i < 5:  # 只显示前5个路径作为示例
                print(f"条目 {i+1}:")
                print(f"  原始URI: {resource}")
                print(f"  方法1 (直接截取): {path1}")
                print(f"  方法2 (pathlib): {path2}")
                print()
    
    if len(entries) > 5:
        print(f"... 还有 {len(entries) - 5} 个条目")
        print()
    
    # 过滤掉非项目文件 (如系统文件)
    project_paths = []
    system_paths = []
    
    for path in paths:
        if path.startswith("/Applications/") or path.startswith("/System/") or "node_modules" in path:
            system_paths.append(path)
        else:
            project_paths.append(path)
    
    print(f"项目文件路径: {len(project_paths)} 个")
    print(f"系统/依赖文件路径: {len(system_paths)} 个")
    print()
    
    # 计算最长公共路径
    if project_paths:
        try:
            common_path = os.path.commonpath(project_paths)
            print(f"项目文件的最长公共路径: {common_path}")
        except ValueError as e:
            print(f"计算项目文件公共路径时出错: {e}")
            # 尝试使用commonprefix作为备选
            common_prefix = os.path.commonprefix(project_paths)
            print(f"项目文件的公共前缀: {common_prefix}")
    
    if paths:  # 包含所有文件
        try:
            all_common_path = os.path.commonpath(paths)
            print(f"所有文件的最长公共路径: {all_common_path}")
        except ValueError as e:
            print(f"计算所有文件公共路径时出错: {e}")
            all_common_prefix = os.path.commonprefix(paths)
            print(f"所有文件的公共前缀: {all_common_prefix}")
    
    print()
    print("=== 详细路径分析 ===")
    print("项目文件路径:")
    for i, path in enumerate(project_paths[:10]):  # 显示前10个
        print(f"  {i+1}. {path}")
    
    if len(project_paths) > 10:
        print(f"  ... 还有 {len(project_paths) - 10} 个项目文件")
    
    if system_paths:
        print("\n系统/依赖文件路径:")
        for i, path in enumerate(system_paths[:5]):  # 显示前5个
            print(f"  {i+1}. {path}")
        if len(system_paths) > 5:
            print(f"  ... 还有 {len(system_paths) - 5} 个系统文件")

if __name__ == "__main__":
    analyze_history_entries()