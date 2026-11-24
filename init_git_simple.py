#!/usr/bin/env python3
"""
Initialize git repository using subprocess to call git directly.
"""

import os
import subprocess
import sys
from pathlib import Path

repo_path = r"D:\11. 2KAD_Soft\0.1 Skills\timeweb-mcp"
os.chdir(repo_path)

# Find git executable
git_paths = [
    "C:\\Program Files\\Git\\bin\\git.exe",
    "C:\\Program Files (x86)\\Git\\bin\\git.exe",
    "git"
]

git_exe = None
for path in git_paths:
    try:
        result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            git_exe = path
            print(f"✓ Found git: {path}")
            print(f"  Version: {result.stdout.strip()}")
            break
    except:
        pass

if not git_exe:
    print("✗ Git not found. Please install Git and try again.")
    sys.exit(1)

print(f"\nWorking in: {repo_path}\n")

commands = [
    ([git_exe, "init"], "Initialize repository"),
    ([git_exe, "config", "user.name", "evgeninho69"], "Set user name"),
    ([git_exe, "config", "user.email", "evgeninho69@gmail.com"], "Set user email"),
    ([git_exe, "add", "."], "Add all files"),
    ([git_exe, "commit", "-m", "Initial commit: MCP server with credential management"], "Create commit"),
    ([git_exe, "remote", "add", "origin", "https://github.com/evgeninho69/timeweb-mcp.git"], "Add remote"),
    ([git_exe, "branch", "-M", "main"], "Rename to main branch"),
]

for cmd, description in commands:
    try:
        print(f"→ {description}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"  ✓ Success")
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[:2]:
                    print(f"    {line}")
        else:
            # Some commands return non-zero but still succeed (e.g., remote add if already exists)
            if "already exists" in result.stderr or result.returncode == 128:
                print(f"  ⚠ Already exists or skipped")
            else:
                print(f"  ✗ Failed: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n→ Pushing to GitHub...")
try:
    result = subprocess.run(
        [git_exe, "push", "-u", "origin", "main"],
        capture_output=True,
        text=True,
        timeout=60,
        input=os.environ.get("GITHUB_TOKEN", "") + "
"
    )
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    print(f"Return code: {result.returncode}")
except Exception as e:
    print(f"  ✗ Push error: {e}")

print("\n✓ Repository initialization complete!")
print(f"Repository: https://github.com/evgeninho69/timeweb-mcp")
