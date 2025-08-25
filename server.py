#!/usr/bin/env python3
"""
Simple API server to serve Cursor chat data for the web interface.
"""

import json
import uuid
import logging
import datetime
import os
import platform
import sqlite3
import argparse
import pathlib
from collections import defaultdict
from typing import Dict, Any, Iterable
from pathlib import Path
from flask import Flask, Response, jsonify, send_from_directory, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='frontend/build')
CORS(app)

# 全局变量：当前暂存的workspace_id
current_workspace_id = None

################################################################################
# Cursor storage roots
################################################################################
def cursor_root() -> pathlib.Path:
    h = pathlib.Path.home()
    s = platform.system()
    if s == "Darwin":   return h / "Library" / "Application Support" / "Cursor"
    if s == "Windows":  return h / "AppData" / "Roaming" / "Cursor"
    if s == "Linux":    return h / ".config" / "Cursor"
    raise RuntimeError(f"Unsupported OS: {s}")

################################################################################
# Helpers
################################################################################
def j(cur: sqlite3.Cursor, table: str, key: str):
    cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
    row = cur.fetchone()
    if row:
        try:    return json.loads(row[0])
        except Exception as e: 
            logger.debug(f"Failed to parse JSON for {key}: {e}")
    return None

def iter_bubbles_from_disk_kv(db: pathlib.Path) -> Iterable[tuple[str,str,str,str]]:
    """Yield (composerId, role, text, db_path) from cursorDiskKV table."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cursorDiskKV'")
        if not cur.fetchone():
            con.close()
            return
        
        cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'bubbleId:%'")
    except sqlite3.DatabaseError as e:
        logger.debug(f"Database error with {db}: {e}")
        return
    
    db_path_str = str(db)
    
    for k, v in cur.fetchall():
        try:
            if v is None:
                continue
                
            b = json.loads(v)
        except Exception as e:
            logger.debug(f"Failed to parse bubble JSON for key {k}: {e}")
            continue
        
        txt = (b.get("text") or b.get("richText") or "").strip()
        if not txt:         continue
        role = "user" if b.get("type") == 1 else "assistant"
        composerId = k.split(":")[1]  # Format is bubbleId:composerId:bubbleId
        yield composerId, role, txt, db_path_str
    
    con.close()

def iter_chat_from_item_table(db: pathlib.Path) -> Iterable[tuple[str,str,str,str]]:
    """Yield (composerId, role, text, db_path) from ItemTable."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
        
        # Try to get chat data from workbench.panel.aichat.view.aichat.chatdata
        chat_data = j(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata")
        if chat_data and "tabs" in chat_data:
            for tab in chat_data.get("tabs", []):
                tab_id = tab.get("tabId", "unknown")
                for bubble in tab.get("bubbles", []):
                    bubble_type = bubble.get("type")
                    if not bubble_type:
                        continue
                    
                    # Extract text from various possible fields
                    text = ""
                    if "text" in bubble:
                        text = bubble["text"]
                    elif "content" in bubble:
                        text = bubble["content"]
                    
                    if text and isinstance(text, str):
                        role = "user" if bubble_type == "user" else "assistant"
                        yield tab_id, role, text, str(db)
        
        # Check for composer data
        composer_data = j(cur, "ItemTable", "composer.composerData")
        if composer_data:
            for comp in composer_data.get("allComposers", []):
                comp_id = comp.get("composerId", "unknown")
                messages = comp.get("messages", [])
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if content:
                        yield comp_id, role, content, str(db)
        
        # Also check for aiService entries
        for key_prefix in ["aiService.prompts", "aiService.generations"]:
            try:
                cur.execute("SELECT key, value FROM ItemTable WHERE key LIKE ?", (f"{key_prefix}%",))
                for k, v in cur.fetchall():
                    try:
                        data = json.loads(v)
                        if isinstance(data, list):
                            for item in data:
                                if "id" in item and "text" in item:
                                    role = "user" if "prompts" in key_prefix else "assistant"
                                    yield item.get("id", "unknown"), role, item.get("text", ""), str(db)
                    except json.JSONDecodeError:
                        continue
            except sqlite3.Error:
                continue
    
    except sqlite3.DatabaseError as e:
        logger.debug(f"Database error in ItemTable with {db}: {e}")
        return
    finally:
        try:
            con.close()
        except (NameError, UnboundLocalError):
            pass

def iter_composer_data(db: pathlib.Path) -> Iterable[tuple[str,dict,str]]:
    """Yield (composerId, composerData, db_path) from cursorDiskKV table."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cursorDiskKV'")
        if not cur.fetchone():
            con.close()
            return
        
        cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'")
    except sqlite3.DatabaseError as e:
        logger.debug(f"Database error with {db}: {e}")
        return
    
    db_path_str = str(db)
    
    for k, v in cur.fetchall():
        try:
            if v is None:
                continue
                
            composer_data = json.loads(v)
            composer_id = k.split(":")[1]
            yield composer_id, composer_data, db_path_str
            
        except Exception as e:
            logger.debug(f"Failed to parse composer data for key {k}: {e}")
            continue
    
    con.close()

################################################################################
# Workspace discovery
################################################################################
def workspaces(base: pathlib.Path):
    ws_root = base / "User" / "workspaceStorage"
    if not ws_root.exists():
        return
    for folder in ws_root.iterdir():
        db = folder / "state.vscdb"
        if db.exists():
            yield folder.name, db

def extract_project_name_from_path(root_path, debug=False):
    """
    Extract a project name from a path, skipping user directories.
    This function is designed to be cross-platform.
    """
    if not root_path or root_path in ('/', '\\'):
        return "Root"
    
    # Normalize the path and split into parts
    try:
        p = pathlib.Path(root_path)
        path_parts = [part for part in p.parts if part and part != p.drive]
    except Exception as e:
        logger.debug(f"Could not parse path with pathlib: {e}. Falling back to string split.")
        # Fallback for unusual paths
        root_path = root_path.replace('\\', '/').strip('/')
        path_parts = [part for part in root_path.split('/') if part]

    if not path_parts:
        return "Root"

    # Get home directory and current username
    home_dir = pathlib.Path.home()
    current_username = home_dir.name

    # Check if the path is within the user's home directory
    is_in_home = False
    try:
        is_in_home = p.is_relative_to(home_dir)
    except (ValueError, TypeError): # In Python < 3.9 is_relative_to doesn't exist
        try:
            home_dir.joinpath(p.relative_to(home_dir))
            is_in_home = True
        except ValueError:
            is_in_home = False


    # If it's just the home directory, return "Home Directory"
    if p == home_dir:
        return "Home Directory"

    project_name = None

    # Define known project markers
    known_project_markers = ['.git', 'pyproject.toml', 'package.json', 'go.mod', 'Cargo.toml']
    
    # Check for project markers in the path
    for i in range(len(path_parts) - 1, -1, -1):
        current_path = p.parents[len(p.parents) - i -1]
        if any((current_path / marker).exists() for marker in known_project_markers):
            project_name = path_parts[i]
            if debug:
                logger.debug(f"Found project marker, setting project name to: {project_name}")
            break
    
    # If no marker found, use heuristics
    if not project_name:
        # Use the last part of the path as a candidate
        candidate = path_parts[-1]
        
        # Avoid common non-project directory names
        non_project_dirs = ['Documents', 'Projects', 'Code', 'workspace', 'repos', 'git', 'src', 'codebase', 'Downloads', 'Desktop', 'Library', 'Applications', 'System', 'var', 'opt', 'tmp']
        
        if candidate not in non_project_dirs and candidate != current_username:
            project_name = candidate
            if debug:
                logger.debug(f"Using last path component as project name: {project_name}")
        # If the last part is a non-project dir, try the one before it
        elif len(path_parts) > 1 and path_parts[-2] not in non_project_dirs and path_parts[-2] != current_username:
             project_name = path_parts[-1]
             if debug:
                logger.debug(f"Using last path component as project name because parent is also a project: {project_name}")

    # Final check to avoid returning the username
    if project_name == current_username:
        project_name = "Home Directory"

    return project_name if project_name else "Unknown Project"

def workspace_info(db: pathlib.Path):
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()

        # Get file paths from history entries to extract the project name
        proj = {"name": "(unknown)", "rootPath": "(unknown)"}
        ents = j(cur,"ItemTable","history.entries") or []
        
        # Extract file paths from history entries, converting URIs to paths
        paths = []
        for e in ents:
            resource = e.get("editor", {}).get("resource", "")
            if resource and resource.startswith("file:///"):
                try:
                    # Correctly handle URI to path conversion
                    path_str = pathlib.Path(urllib.parse.unquote(resource[len("file:///"):])).as_posix()
                    paths.append(path_str)
                except Exception as e:
                    logger.debug(f"Could not parse resource URI {resource}: {e}")

        # If we found file paths, extract the project name using the longest common prefix
        if paths:
            logger.debug(f"Found {len(paths)} paths in history entries")
            
            # Use os.path.commonpath to handle cross-platform paths correctly
            common_prefix = os.path.commonpath(paths)
            logger.debug(f"Common prefix: {common_prefix}")
            
            if common_prefix:
                project_root = common_prefix
                logger.debug(f"Project root from common prefix: {project_root}")
                
                # Extract the project name using the helper function
                project_name = extract_project_name_from_path(project_root, debug=True)
                
                proj = {"name": project_name, "rootPath": pathlib.Path(project_root).as_posix()}
        
        # Try backup methods if we didn't get a project name
        if proj["name"] == "(unknown)":
            logger.debug("Trying backup methods for project name")
            
            # Check debug.selectedroot as a fallback
            selected_root = j(cur, "ItemTable", "debug.selectedroot")
            if selected_root and isinstance(selected_root, str) and selected_root.startswith("file:///"):
                try:
                    path = pathlib.Path(urllib.parse.unquote(selected_root[len("file:///"):])).as_posix()
                    if path:
                        root_path = path
                        logger.debug(f"Project root from debug.selectedroot: {root_path}")
                        
                        # Extract the project name using the helper function
                        project_name = extract_project_name_from_path(root_path, debug=True)
                        
                        if project_name:
                            proj = {"name": project_name, "rootPath": root_path}
                except Exception as e:
                    logger.debug(f"Could not parse selected_root URI {selected_root}: {e}")):])
        
        # If we found file paths, extract the project name using the longest common prefix
        if paths:
            logger.debug(f"Found {len(paths)} paths in history entries")
            
            # Get the longest common prefix
            common_prefix = os.path.commonprefix(paths)
            logger.debug(f"Common prefix: {common_prefix}")
            
            # Find the last directory separator in the common prefix
            last_separator_index = common_prefix.rfind('/')
            if last_separator_index > 0:
                project_root = common_prefix[:last_separator_index]
                logger.debug(f"Project root from common prefix: {project_root}")
                
                # Extract the project name using the helper function
                project_name = extract_project_name_from_path(project_root, debug=True)
                
                proj = {"name": project_name, "rootPath": "/" + project_root.lstrip('/')}
        
        # Try backup methods if we didn't get a project name
        if proj["name"] == "(unknown)":
            logger.debug("Trying backup methods for project name")
            
            # Check debug.selectedroot as a fallback
            selected_root = j(cur, "ItemTable", "debug.selectedroot")
            if selected_root and isinstance(selected_root, str) and selected_root.startswith("file:///"):
                path = selected_root[len("file:///"):]
                if path:
                    root_path = "/" + path.strip("/")
                    logger.debug(f"Project root from debug.selectedroot: {root_path}")
                    
                    # Extract the project name using the helper function
                    project_name = extract_project_name_from_path(root_path, debug=True)
                    
                    if project_name:
                        proj = {"name": project_name, "rootPath": root_path}

        # composers meta
        comp_meta={}
        cd = j(cur,"ItemTable","composer.composerData") or {}
        for c in cd.get("allComposers",[]):
            comp_meta[c["composerId"]] = {
                "title": c.get("name","(untitled)"),
                "createdAt": c.get("createdAt"),
                "lastUpdatedAt": c.get("lastUpdatedAt")
            }
        
        # Try to get composer info from workbench.panel.aichat.view.aichat.chatdata
        chat_data = j(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata") or {}
        for tab in chat_data.get("tabs", []):
            tab_id = tab.get("tabId")
            if tab_id and tab_id not in comp_meta:
                comp_meta[tab_id] = {
                    "title": f"Chat {tab_id[:8]}",
                    "createdAt": None,
                    "lastUpdatedAt": None
                }
    except sqlite3.DatabaseError as e:
        logger.debug(f"Error getting workspace info from {db}: {e}")
        proj = {"name": "(unknown)", "rootPath": "(unknown)"}
        comp_meta = {}
    finally:
        try:
            con.close()
        except (NameError, UnboundLocalError):
            pass
            
    return proj, comp_meta

################################################################################
# GlobalStorage
################################################################################
def global_storage_path(base: pathlib.Path) -> pathlib.Path | None:
    """Return path to the global storage state.vscdb."""
    global_db = base / "User" / "globalStorage" / "state.vscdb"
    if global_db.exists():
        return global_db
    
    # Legacy paths
    g_dirs = [base/"User"/"globalStorage"/"cursor.cursor",
              base/"User"/"globalStorage"/"cursor"]
    for d in g_dirs:
        if d.exists():
            for file in d.glob("*.sqlite"):
                return file
    
    return None

################################################################################
# Extraction pipeline
################################################################################
def extract_chats() -> list[Dict[str,Any]]:
    root = cursor_root()
    logger.debug(f"Using Cursor root: {root}")

    # Diagnostic: Check for AI-related keys in the first workspace
    if os.environ.get("CURSOR_CHAT_DIAGNOSTICS"):
        try:
            first_ws = next(workspaces(root))
            if first_ws:
                ws_id, db = first_ws
                logger.debug(f"\n--- DIAGNOSTICS for workspace {ws_id} ---")
                con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                cur = con.cursor()
                
                # List all tables
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cur.fetchall()]
                logger.debug(f"Tables in workspace DB: {tables}")
                
                # Search for AI-related keys
                if "ItemTable" in tables:
                    for pattern in ['%ai%', '%chat%', '%composer%', '%prompt%', '%generation%']:
                        cur.execute("SELECT key FROM ItemTable WHERE key LIKE ?", (pattern,))
                        keys = [row[0] for row in cur.fetchall()]
                        if keys:
                            logger.debug(f"Keys matching '{pattern}': {keys}")
                
                con.close()
                
            # Check global storage
            global_db = global_storage_path(root)
            if global_db:
                logger.debug(f"\n--- DIAGNOSTICS for global storage ---")
                con = sqlite3.connect(f"file:{global_db}?mode=ro", uri=True)
                cur = con.cursor()
                
                # List all tables
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cur.fetchall()]
                logger.debug(f"Tables in global DB: {tables}")
                
                # Search for AI-related keys in ItemTable
                if "ItemTable" in tables:
                    for pattern in ['%ai%', '%chat%', '%composer%', '%prompt%', '%generation%']:
                        cur.execute("SELECT key FROM ItemTable WHERE key LIKE ?", (pattern,))
                        keys = [row[0] for row in cur.fetchall()]
                        if keys:
                            logger.debug(f"Keys matching '{pattern}': {keys}")
                
                # Check for keys in cursorDiskKV
                if "cursorDiskKV" in tables:
                    cur.execute("SELECT DISTINCT substr(key, 1, instr(key, ':') - 1) FROM cursorDiskKV")
                    prefixes = [row[0] for row in cur.fetchall()]
                    logger.debug(f"Key prefixes in cursorDiskKV: {prefixes}")
                
                con.close()
            
            logger.debug("\n--- END DIAGNOSTICS ---\n")
        except Exception as e:
            logger.debug(f"Error in diagnostics: {e}")

    # map lookups
    ws_proj  : Dict[str,Dict[str,Any]] = {}
    comp_meta: Dict[str,Dict[str,Any]] = {}
    comp2ws  : Dict[str,str]           = {}
    sessions : Dict[str,Dict[str,Any]] = defaultdict(lambda: {"messages":[]})

    # 1. Process workspace DBs first
    logger.debug("Processing workspace databases...")
    ws_count = 0
    for ws_id, db in workspaces(root):
        ws_count += 1
        logger.debug(f"Processing workspace {ws_id} - {db}")
        proj, meta = workspace_info(db)
        ws_proj[ws_id] = proj
        for cid, m in meta.items():
            comp_meta[cid] = m
            comp2ws[cid] = ws_id
        
        # Extract chat data from workspace's state.vscdb
        msg_count = 0
        for cid, role, text, db_path in iter_chat_from_item_table(db):
            # Add the message
            sessions[cid]["messages"].append({"role": role, "content": text})
            # Make sure to record the database path
            if "db_path" not in sessions[cid]:
                sessions[cid]["db_path"] = db_path
            msg_count += 1
            if cid not in comp_meta:
                comp_meta[cid] = {"title": f"Chat {cid[:8]}", "createdAt": None, "lastUpdatedAt": None}
                comp2ws[cid] = ws_id
        logger.debug(f"  - Extracted {msg_count} messages from workspace {ws_id}")
    
    logger.debug(f"Processed {ws_count} workspaces")

    # 2. Process global storage
    global_db = global_storage_path(root)
    if global_db:
        logger.debug(f"Processing global storage: {global_db}")
        # Extract bubbles from cursorDiskKV
        msg_count = 0
        for cid, role, text, db_path in iter_bubbles_from_disk_kv(global_db):
            sessions[cid]["messages"].append({"role": role, "content": text})
            # Record the database path
            if "db_path" not in sessions[cid]:
                sessions[cid]["db_path"] = db_path
            msg_count += 1
            if cid not in comp_meta:
                comp_meta[cid] = {"title": f"Chat {cid[:8]}", "createdAt": None, "lastUpdatedAt": None}
                comp2ws[cid] = "(global)"
        logger.debug(f"  - Extracted {msg_count} messages from global cursorDiskKV bubbles")
        
        # Extract composer data
        comp_count = 0
        for cid, data, db_path in iter_composer_data(global_db):
            if cid not in comp_meta:
                created_at = data.get("createdAt")
                comp_meta[cid] = {
                    "title": f"Chat {cid[:8]}",
                    "createdAt": created_at,
                    "lastUpdatedAt": created_at
                }
                comp2ws[cid] = "(global)"
            
            # Record the database path
            if "db_path" not in sessions[cid]:
                sessions[cid]["db_path"] = db_path
                
            # Extract conversation from composer data
            conversation = data.get("conversation", [])
            if conversation:
                msg_count = 0
                for msg in conversation:
                    msg_type = msg.get("type")
                    if msg_type is None:
                        continue
                    
                    # Type 1 = user, Type 2 = assistant
                    role = "user" if msg_type == 1 else "assistant"
                    content = msg.get("text", "")
                    if content and isinstance(content, str):
                        sessions[cid]["messages"].append({"role": role, "content": content})
                        msg_count += 1
                
                if msg_count > 0:
                    comp_count += 1
                    logger.debug(f"  - Added {msg_count} messages from composer {cid[:8]}")
        
        if comp_count > 0:
            logger.debug(f"  - Extracted data from {comp_count} composers in global cursorDiskKV")
        
        # Also try ItemTable in global DB
        try:
            con = sqlite3.connect(f"file:{global_db}?mode=ro", uri=True)
            chat_data = j(con.cursor(), "ItemTable", "workbench.panel.aichat.view.aichat.chatdata")
            if chat_data:
                msg_count = 0
                for tab in chat_data.get("tabs", []):
                    tab_id = tab.get("tabId")
                    if tab_id and tab_id not in comp_meta:
                        comp_meta[tab_id] = {
                            "title": f"Global Chat {tab_id[:8]}",
                            "createdAt": None,
                            "lastUpdatedAt": None
                        }
                        comp2ws[tab_id] = "(global)"
                    
                    for bubble in tab.get("bubbles", []):
                        content = ""
                        if "text" in bubble:
                            content = bubble["text"]
                        elif "content" in bubble:
                            content = bubble["content"]
                        
                        if content and isinstance(content, str):
                            role = "user" if bubble.get("type") == "user" else "assistant"
                            sessions[tab_id]["messages"].append({"role": role, "content": content})
                            msg_count += 1
                logger.debug(f"  - Extracted {msg_count} messages from global chat data")
            con.close()
        except Exception as e:
            logger.debug(f"Error processing global ItemTable: {e}")

    # 3. Build final list
    out = []
    for cid, data in sessions.items():
        if not data["messages"]:
            continue
        ws_id = comp2ws.get(cid, "(unknown)")
        project = ws_proj.get(ws_id, {"name": "(unknown)", "rootPath": "(unknown)"})
        meta = comp_meta.get(cid, {"title": "(untitled)", "createdAt": None, "lastUpdatedAt": None})
        
        # Create the output object with the db_path included
        chat_data = {
            "project": project,
            "session": {"composerId": cid, **meta},
            "messages": data["messages"],
            "workspace_id": ws_id,
        }
        
        # Add the database path if available
        if "db_path" in data:
            chat_data["db_path"] = data["db_path"]
            
        out.append(chat_data)
    
    # Sort by last updated time if available
    out.sort(key=lambda s: s["session"].get("lastUpdatedAt") or 0, reverse=True)
    logger.debug(f"Total chat sessions extracted: {len(out)}")
    return out

def extract_project_from_git_repos(workspace_id, debug=False):
    """
    Extract project name from the git repositories in a workspace.
    Returns None if no repositories found or unable to access the DB.
    """
    if not workspace_id or workspace_id == "unknown" or workspace_id == "(unknown)" or workspace_id == "(global)":
        if debug:
            logger.debug(f"Invalid workspace ID: {workspace_id}")
        return None
        
    # Find the workspace DB
    cursor_base = cursor_root()
    workspace_db_path = cursor_base / "User" / "workspaceStorage" / workspace_id / "state.vscdb"
    
    if not workspace_db_path.exists():
        if debug:
            logger.debug(f"Workspace DB not found for ID: {workspace_id}")
        return None
        
    try:
        # Connect to the workspace DB
        if debug:
            logger.debug(f"Connecting to workspace DB: {workspace_db_path}")
        con = sqlite3.connect(f"file:{workspace_db_path}?mode=ro", uri=True)
        cur = con.cursor()
        
        # Look for git repositories
        git_data = j(cur, "ItemTable", "scm:view:visibleRepositories")
        if not git_data or not isinstance(git_data, dict) or 'all' not in git_data:
            if debug:
                logger.debug(f"No git repositories found in workspace {workspace_id}, git_data: {git_data}")
            con.close()
            return None
            
        # Extract repo paths from the 'all' key
        repos = git_data.get('all', [])
        if not repos or not isinstance(repos, list):
            if debug:
                logger.debug(f"No repositories in 'all' key for workspace {workspace_id}, repos: {repos}")
            con.close()
            return None
            
        if debug:
            logger.debug(f"Found {len(repos)} git repositories in workspace {workspace_id}: {repos}")
            
        # Process each repo path
        for repo in repos:
            if not isinstance(repo, str):
                continue
                
            # Look for git:Git:file:/// pattern
            if "git:Git:file:///" in repo:
                # Extract the path part
                path = repo.split("file:///")[-1]
                path_parts = [p for p in path.split('/') if p]
                
                if path_parts:
                    # Use the last part as the project name
                    project_name = path_parts[-1]
                    if debug:
                        logger.debug(f"Found project name '{project_name}' from git repo in workspace {workspace_id}")
                    con.close()
                    return project_name
            else:
                if debug:
                    logger.debug(f"No 'git:Git:file:///' pattern in repo: {repo}")
                    
        if debug:
            logger.debug(f"No suitable git repos found in workspace {workspace_id}")
        con.close()
    except Exception as e:
        if debug:
            logger.debug(f"Error extracting git repos from workspace {workspace_id}: {e}")
        return None
        
    return None

def format_chat_for_frontend(chat):
    """Format the chat data to match what the frontend expects."""
    try:
        # Generate a unique ID for this chat if it doesn't have one
        session_id = str(uuid.uuid4())
        if 'session' in chat and chat['session'] and isinstance(chat['session'], dict):
            session_id = chat['session'].get('composerId', session_id)
        
        # Format date from createdAt timestamp or use current date
        date = int(datetime.datetime.now().timestamp())
        if 'session' in chat and chat['session'] and isinstance(chat['session'], dict):
            created_at = chat['session'].get('createdAt')
            if created_at and isinstance(created_at, (int, float)):
                # Convert from milliseconds to seconds
                date = created_at / 1000
        
        # Ensure project has expected fields
        project = chat.get('project', {})
        if not isinstance(project, dict):
            project = {}
            
        # Get workspace_id from chat
        workspace_id = chat.get('workspace_id', 'unknown')
        
        # Get the database path information
        db_path = chat.get('db_path', 'Unknown database path')
        
        # If project name is a username or unknown, try to extract a better name from rootPath
        if project.get('rootPath'):
            root_path = pathlib.Path(project.get('rootPath'))
            current_name = project.get('name', '')
            username = os.path.basename(os.path.expanduser('~'))
            
            # Check if project name is username or unknown or very generic
            if (current_name == username or 
                current_name == '(unknown)' or 
                current_name == 'Root' or
                # Check if rootPath is the user's home directory
                (root_path.is_dir() and root_path.samefile(pathlib.Path.home()))):
                
                # Try to extract a better name from the path
                project_name = extract_project_name_from_path(str(root_path), debug=False)
                
                # Only use the new name if it's meaningful
                if (project_name and 
                    project_name != 'Unknown Project' and 
                    project_name != username and
                    project_name not in ['Documents', 'Downloads', 'Desktop']):
                    
                    logger.debug(f"Improved project name from '{current_name}' to '{project_name}'")
                    project['name'] = project_name
                elif 'codebase' in root_path.parts:
                    # Special case for paths containing 'codebase'
                    try:
                        codebase_index = root_path.parts.index('codebase')
                        if codebase_index + 1 < len(root_path.parts):
                            project['name'] = root_path.parts[codebase_index + 1]
                            logger.debug(f"Set project name to specific codebase subdirectory: {project['name']}")
                        else:
                            project['name'] = "cursor-view"  # Current project as default
                    except ValueError:
                        pass

        # If the project doesn't have a rootPath or it's very generic, enhance it with workspace_id
        if not project.get('rootPath') or project.get('rootPath') in ['/', str(pathlib.Path.home().parent)]:
            if workspace_id != 'unknown':
                # Use workspace_id to create a more specific path
                if not project.get('rootPath'):
                    project['rootPath'] = str(pathlib.Path("/workspace") / workspace_id)
                else:
                    project['rootPath'] = str(pathlib.Path(project.get('rootPath')) / "workspace" / workspace_id)

        # FALLBACK: If project name is still generic, try to extract it from git repositories
        if project.get('name') in ['Home Directory', '(unknown)']:
            git_project_name = extract_project_from_git_repos(workspace_id, debug=True)
            if git_project_name:
                logger.debug(f"Improved project name from '{project.get('name')}' to '{git_project_name}' using git repo")
                project['name'] = git_project_name
        
        # Add workspace_id to the project data explicitly
        project['workspace_id'] = workspace_id
            
        # Ensure messages exist and are properly formatted
        messages = chat.get('messages', [])
        if not isinstance(messages, list):
            messages = []
        
        # Create properly formatted chat object
        return {
            'project': project,
            'messages': messages,
            'date': date,
            'session_id': session_id,
            'workspace_id': workspace_id,
            'db_path': db_path  # Include the database path in the output
        }
    except Exception as e:
        logger.error(f"Error formatting chat: {e}")
        # Return a minimal valid object if there's an error
        return {
            'project': {'name': 'Error', 'rootPath': '/'},
            'messages': [],
            'date': int(datetime.datetime.now().timestamp()),
            'session_id': str(uuid.uuid4()),
            'workspace_id': 'error',
            'db_path': 'Error retrieving database path'
        }

@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Get all chat sessions."""
    try:
        logger.info(f"Received request for chats from {request.remote_addr}")
        chats = extract_chats()
        logger.info(f"Retrieved {len(chats)} chats")
        
        # Format each chat for the frontend
        formatted_chats = []
        for chat in chats:
            try:
                formatted_chat = format_chat_for_frontend(chat)
                formatted_chats.append(formatted_chat)
            except Exception as e:
                logger.error(f"Error formatting individual chat: {e}")
                # Skip this chat if it can't be formatted
                continue
        
        logger.info(f"Returning {len(formatted_chats)} formatted chats")
        return jsonify(formatted_chats)
    except Exception as e:
        logger.error(f"Error in get_chats: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/<session_id>', methods=['GET'])
def get_chat(session_id):
    """Get a specific chat session by ID."""
    try:
        logger.info(f"Received request for chat {session_id} from {request.remote_addr}")
        chats = extract_chats()
        
        for chat in chats:
            # Check for a matching composerId safely
            if 'session' in chat and chat['session'] and isinstance(chat['session'], dict):
                if chat['session'].get('composerId') == session_id:
                    formatted_chat = format_chat_for_frontend(chat)
                    return jsonify(formatted_chat)
        
        logger.warning(f"Chat with ID {session_id} not found")
        return jsonify({"error": "Chat not found"}), 404
    except Exception as e:
        logger.error(f"Error in get_chat: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/send-to-cursor', methods=['POST'])
def send_to_cursor():
    """发送消息到Cursor应用"""
    global current_workspace_id
    
    try:
        logger.info(f"Received send-to-cursor request from {request.remote_addr}")
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field in request"}), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # 获取workspace_id和rootPath
        workspace_id = data.get('workspace_id')
        root_path = data.get('rootPath')
        
        logger.info(f"Attempting to send message to Cursor: {message[:100]}...")
        logger.info(f"Workspace ID: {workspace_id}, Root Path: {root_path}")
        logger.info(f"Current workspace ID: {current_workspace_id}")
        
        # 检查pyautogui模块是否可用
        try:
            import sys
            import os
            # 添加当前目录到Python路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from pyautogu import receive_from_app
            from pyautogu import switch_cursor_project
        except ImportError as e:
            logger.error(f"pyautogu module not available: {e}")
            return jsonify({"error": "Cursor automation not available. Please ensure pyautogu.py is properly configured."}), 500
        
        # 检查workspace_id是否与当前暂存的一致
        project_switched = False
        if workspace_id and workspace_id != current_workspace_id:
            logger.info(f"Workspace changed from {current_workspace_id} to {workspace_id}")
            
            # 如果有rootPath，则切换到目标项目
            if root_path:
                logger.info(f"Switching to project: {root_path}")
                switch_success = switch_cursor_project(root_path)
                if not switch_success:
                    logger.error(f"Failed to switch to project: {root_path}")
                    return jsonify({"error": f"Failed to switch to project: {root_path}"}), 500
                
                # 更新当前workspace_id
                current_workspace_id = workspace_id
                logger.info(f"Successfully switched to workspace: {workspace_id}")
                project_switched = True
            else:
                logger.warning("Workspace ID provided but no rootPath available for switching")
        
        # 调用pyautogui发送消息到Cursor
        # 如果刚切换了项目，跳过激活步骤避免重复操作
        success = receive_from_app(message, skip_activation=project_switched)
        
        if success:
            logger.info("Message successfully sent to Cursor")
            return jsonify({"success": True, "message": "Message sent to Cursor successfully"})
        else:
            logger.error("Failed to send message to Cursor")
            return jsonify({"error": "Failed to send message to Cursor. Please ensure Cursor is running and accessible."}), 500
            
    except Exception as e:
        logger.error(f"Error in send_to_cursor: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/chat/<session_id>/export', methods=['GET'])
def export_chat(session_id):
    """Export a specific chat session as standalone HTML or JSON."""
    try:
        logger.info(f"Received request to export chat {session_id} from {request.remote_addr}")
        export_format = request.args.get('format', 'html').lower()
        chats = extract_chats()
        
        for chat in chats:
            # Check for a matching composerId safely
            if 'session' in chat and chat['session'] and isinstance(chat['session'], dict):
                if chat['session'].get('composerId') == session_id:
                    formatted_chat = format_chat_for_frontend(chat)
                    
                    if export_format == 'json':
                        # Export as JSON
                        return Response(
                            json.dumps(formatted_chat, indent=2),
                            mimetype="application/json; charset=utf-8",
                            headers={
                                "Content-Disposition": f'attachment; filename="cursor-chat-{session_id[:8]}.json"',
                                "Cache-Control": "no-store",
                            },
                        )
                    else:
                        # Default to HTML export
                        html_content = generate_standalone_html(formatted_chat)
                        return Response(
                            html_content,
                            mimetype="text/html; charset=utf-8",
                            headers={
                                "Content-Disposition": f'attachment; filename="cursor-chat-{session_id[:8]}.html"',
                                "Content-Length": str(len(html_content)),
                                "Cache-Control": "no-store",
                            },
                        )
        
        logger.warning(f"Chat with ID {session_id} not found for export")
        return jsonify({"error": "Chat not found"}), 404
    except Exception as e:
        logger.error(f"Error in export_chat: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def generate_standalone_html(chat):
    """Generate a standalone HTML representation of the chat."""
    logger.info(f"Generating HTML for session ID: {chat.get('session_id', 'N/A')}")
    try:
        # Format date for display
        date_display = "Unknown date"
        if chat.get('date'):
            try:
                date_obj = datetime.datetime.fromtimestamp(chat['date'])
                date_display = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logger.warning(f"Error formatting date: {e}")
        
        # Get project info
        project_name = chat.get('project', {}).get('name', 'Unknown Project')
        project_path = chat.get('project', {}).get('rootPath', 'Unknown Path')
        logger.info(f"Project: {project_name}, Path: {project_path}, Date: {date_display}")
        
        # Build the HTML content
        messages_html = ""
        messages = chat.get('messages', [])
        logger.info(f"Found {len(messages)} messages for the chat.")
        
        if not messages:
            logger.warning("No messages found in the chat object to generate HTML.")
            messages_html = "<p>No messages found in this conversation.</p>"
        else:
            for i, msg in enumerate(messages):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                logger.debug(f"Processing message {i+1}/{len(messages)} - Role: {role}, Content length: {len(content)}")
                
                if not content or not isinstance(content, str):
                    logger.warning(f"Message {i+1} has invalid content: {content}")
                    content = "Content unavailable"
                
                # Simple HTML escaping
                escaped_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                # Convert markdown code blocks (handle potential nesting issues simply)
                processed_content = ""
                in_code_block = False
                for line in escaped_content.split('\n'):
                    if line.strip().startswith("```"):
                        if not in_code_block:
                            processed_content += "<pre><code>"
                            in_code_block = True
                            # Remove the first ``` marker
                            line = line.strip()[3:] 
                        else:
                            processed_content += "</code></pre>\n"
                            in_code_block = False
                            line = "" # Skip the closing ``` line
                    
                    if in_code_block:
                         # Inside code block, preserve spacing and add line breaks
                        processed_content += line + "\n" 
                    else:
                        # Outside code block, use <br> for newlines
                        processed_content += line + "<br>"
                
                # Close any unclosed code block at the end
                if in_code_block:
                    processed_content += "</code></pre>"
                
                avatar = "👤" if role == "user" else "🤖"
                name = "You" if role == "user" else "Cursor Assistant"
                bg_color = "#f0f7ff" if role == "user" else "#f0fff7"
                border_color = "#3f51b5" if role == "user" else "#00796b"
                
                messages_html += f"""
                <div class="message" style="margin-bottom: 20px;">
                    <div class="message-header" style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div class="avatar" style="width: 32px; height: 32px; border-radius: 50%; background-color: {border_color}; color: white; display: flex; justify-content: center; align-items: center; margin-right: 10px;">
                            {avatar}
                        </div>
                        <div class="sender" style="font-weight: bold;">{name}</div>
                    </div>
                    <div class="message-content" style="padding: 15px; border-radius: 8px; background-color: {bg_color}; border-left: 4px solid {border_color}; margin-left: {0 if role == 'user' else '40px'}; margin-right: {0 if role == 'assistant' else '40px'};">
                        {processed_content} 
                    </div>
                </div>
                """

        # Create the complete HTML document
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cursor Chat - {project_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 20px auto; padding: 20px; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .header {{ background: linear-gradient(90deg, #f0f7ff 0%, #f0fff7 100%); color: white; padding: 15px 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
        .chat-info {{ display: flex; flex-wrap: wrap; gap: 10px 20px; margin-bottom: 20px; background-color: #f9f9f9; padding: 12px 15px; border-radius: 8px; font-size: 0.9em; }}
        .info-item {{ display: flex; align-items: center; }}
        .info-label {{ font-weight: bold; margin-right: 5px; color: #555; }}
        pre {{ background-color: #eef; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #ddd; font-family: 'Courier New', Courier, monospace; font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word; }}
        code {{ background-color: transparent; padding: 0; border-radius: 0; font-family: inherit; }}
        .message-content pre code {{ background-color: transparent; }}
        .message-content {{ word-wrap: break-word; overflow-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Cursor Chat: {project_name}</h1>
    </div>
    <div class="chat-info">
        <div class="info-item"><span class="info-label">Project:</span> <span>{project_name}</span></div>
        <div class="info-item"><span class="info-label">Path:</span> <span>{project_path}</span></div>
        <div class="info-item"><span class="info-label">Date:</span> <span>{date_display}</span></div>
        <div class="info-item"><span class="info-label">Session ID:</span> <span>{chat.get('session_id', 'Unknown')}</span></div>
    </div>
    <h2>Conversation History</h2>
    <div class="messages">
{messages_html}
    </div>
    <div style="margin-top: 30px; font-size: 12px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 15px;">
        <a href="https://github.com/saharmor/cursor-view" target="_blank" rel="noopener noreferrer">Exported from Cursor View</a>
    </div>
</body>
</html>"""
        
        logger.info(f"Finished generating HTML. Total length: {len(html)}")
        return html
    except Exception as e:
        logger.error(f"Error generating HTML for session {chat.get('session_id', 'N/A')}: {e}", exc_info=True)
        # Return an HTML formatted error message
        return f"<html><body><h1>Error generating chat export</h1><p>Error: {e}</p></body></html>"

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path and app.static_folder and Path(app.static_folder, path).exists():
        return send_from_directory(app.static_folder, path)
    if app.static_folder:
        return send_from_directory(app.static_folder, 'index.html')
    return "Static folder not configured", 404

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Cursor Chat View server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    logger.info(f"Starting server on port {args.port}")
    app.run(host='127.0.0.1', port=args.port, debug=args.debug)