# Timeweb MCP (stdio)

Local MCP server for Timeweb Cloud via `twc` CLI.

## What you get

- Native MCP stdio server (works with Codex `mcp_servers.<name>.command`)
- Universal tool `timeweb_run_cli` for any `twc` command
- Ready `.env` configuration file
- Common shortcuts for servers/apps/account

## 1) Install dependencies

```powershell
pip install -r requirements.txt
pip install -U twc-cli
```

## 2) Configure Timeweb CLI

```powershell
twc config
```

If `twc` is not in `PATH`, run:

```powershell
& "C:\Users\ZotkinEA\AppData\Roaming\Python\Python313\Scripts\twc.exe" config
```

## 3) Configure `.env`

```powershell
Copy-Item .env.example .env -Force
```

Update values in `.env` if needed.

## 4) Add server to Codex (`~/.codex/config.toml`)

```toml
[mcp_servers.timeweb]
command = "python"
args = ["D:\\11. 2KAD_Soft\\0.1 Skills\\timeweb-mcp\\server.py"]
env = { TIMEWEB_ENV_FILE = "D:\\11. 2KAD_Soft\\0.1 Skills\\timeweb-mcp\\.env" }
startup_timeout_sec = 20
tool_timeout_sec = 240
```

Restart Codex after editing config.

## 5) Quick health check

Ask Codex to call `timeweb_whoami` or `timeweb_account_status`.

## Main tools

- `timeweb_run_cli(args, output_format, cwd)` - run any `twc` command
- `timeweb_account_status()`
- `timeweb_whoami()`
- `timeweb_list_servers(filter_expr)`
- `timeweb_get_server(server_id)`
- `timeweb_start_server(server_ids)`
- `timeweb_stop_server(server_ids, hard)`
- `timeweb_reboot_server(server_ids, hard)`
- `timeweb_list_apps(filter_expr)`
- `timeweb_get_app(app_id, wait_started)`
- `timeweb_create_app(config_path, wait_started)`

## Deployment examples

Create app from current project:

```text
timeweb_run_cli(args=["apps", "create", "./timeweb-app.yaml"], output_format="json")
```

Run any CLI command:

```text
timeweb_run_cli(args=["cluster", "list"], output_format="json")
```
