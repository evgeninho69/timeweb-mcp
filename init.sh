#!/bin/bash
cd "/d/11. 2KAD_Soft/0.1 Skills/timeweb-mcp"
git --version
git status
echo "---"
git init
git add .
git config user.name "evgeninho69"
git config user.email "evgeninho69@gmail.com"
git commit -m "Initial commit: MCP server with credential management"
git remote add origin https://github.com/evgeninho69/timeweb-mcp.git
git branch -M main
git push -u origin main
echo "Done!"
