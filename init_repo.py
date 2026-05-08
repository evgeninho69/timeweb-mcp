#!/usr/bin/env python3
"""
Initialize git repository and push to GitHub without using git command-line.
Uses GitPython library or fallback to manual git operations.
"""

import os
import sys
import json
import base64
import hashlib
import time
from pathlib import Path

# Add repo path
repo_path = r"D:\11. 2KAD_Soft\0.1 Skills\timeweb-mcp"
os.chdir(repo_path)
print(f"Working directory: {repo_path}")

try:
    from git import Repo, Actor
    print("GitPython is available!")
    
    # Initialize repo
    repo = Repo.init(repo_path)
    print("Repository initialized")
    
    # Configure user
    config_writer = repo.config_writer()
    config_writer.set_value("user", "name", "evgeninho69").release()
    config_writer = repo.config_writer()
    config_writer.set_value("user", "email", "evgeninho69@gmail.com").release()
    print("User configured")
    
    # Add all files
    repo.index.add([item.name for item in Path(repo_path).rglob('*') 
                    if item.is_file() and not str(item).endswith(('.git', '.pyc', '__pycache__'))])
    print(f"Added {len(repo.index.entries)} files")
    
    # Create commit
    repo.index.commit("Initial commit: MCP server with credential management")
    print("Commit created")
    
    # Add remote
    if 'origin' not in [r.name for r in repo.remotes]:
        repo.create_remote('origin', 'https://github.com/evgeninho69/timeweb-mcp.git')
        print("Remote 'origin' added")
    
    # Push
    print("Pushing to GitHub...")
    origin = repo.remote('origin')
    origin.push(refspec='refs/heads/master:refs/heads/main')
    print("✓ Successfully pushed to GitHub!")
    
except ImportError:
    print("GitPython not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'GitPython', '-q'])
    print("Retrying with GitPython...")
    exec(open(__file__).read())
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
