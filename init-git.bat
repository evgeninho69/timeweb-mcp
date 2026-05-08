@echo off
setlocal enabledelayedexpansion

set PATH=C:\Program Files\Git\bin;%PATH%
cd /d "%~dp0"

echo === Checking git ===
git --version

echo === Initializing repository ===
git init

echo === Adding files ===
git add .

echo === Setting user config ===
git config user.name "evgeninho69"
git config user.email "evgeninho69@gmail.com"

echo === Making initial commit ===
git commit -m "Initial commit: MCP server for Timeweb with credential management"

echo === Adding remote ===
git remote add origin https://github.com/evgeninho69/timeweb-mcp.git

echo === Pushing to GitHub ===
git branch -M main
git push -u origin main

echo === Done! ===
git log --oneline
