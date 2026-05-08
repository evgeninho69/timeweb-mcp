import json
import logging
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from mcp.server.fastmcp import FastMCP


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into process environment."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        value = value.replace("\\n", "\n")
        os.environ.setdefault(key, value)


def resolve_env_file() -> Path:
    explicit = os.environ.get("TIMEWEB_ENV_FILE")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (Path(__file__).resolve().parent / ".env").resolve()


ENV_FILE = resolve_env_file()
load_dotenv(ENV_FILE)

TIMEWEB_CLI_CMD = os.environ.get("TIMEWEB_CLI_CMD", "twc")
TIMEWEB_CLI_TIMEOUT = int(os.environ.get("TIMEWEB_CLI_TIMEOUT", "120"))
TIMEWEB_CLI_PROFILE = os.environ.get("TIMEWEB_CLI_PROFILE", "").strip()
TIMEWEB_CLI_CONFIG = os.environ.get("TIMEWEB_CLI_CONFIG", "").strip()
TIMEWEB_MCP_NAME = os.environ.get("TIMEWEB_MCP_NAME", "timeweb-mcp")
TIMEWEB_MCP_LOG_LEVEL = os.environ.get("TIMEWEB_MCP_LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, TIMEWEB_MCP_LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("timeweb-mcp")

mcp = FastMCP(
    name=TIMEWEB_MCP_NAME,
    instructions=(
        "Timeweb Cloud MCP server. Use tools to inspect account resources and run any "
        "twc CLI command, including deployment workflows."
    ),
)


def _base_cli_args() -> list[str]:
    args: list[str] = []
    if TIMEWEB_CLI_CONFIG:
        args.extend(["-c", TIMEWEB_CLI_CONFIG])
    if TIMEWEB_CLI_PROFILE:
        args.extend(["-p", TIMEWEB_CLI_PROFILE])
    return args


def _has_output_flag(args: Sequence[str]) -> bool:
    return any(part in ("-o", "--output") for part in args)


def _ensure_cli_available() -> None:
    if shutil.which(TIMEWEB_CLI_CMD) is not None:
        return
    raise RuntimeError(
        f"Timeweb CLI '{TIMEWEB_CLI_CMD}' not found. Install twc-cli and ensure '{TIMEWEB_CLI_CMD}' is in PATH."
    )


def run_twc(
    args: Sequence[str],
    *,
    output_format: str = "json",
    cwd: str | None = None,
) -> dict[str, Any]:
    """Run twc command and return structured execution details."""
    _ensure_cli_available()

    cmd = [TIMEWEB_CLI_CMD, *_base_cli_args(), *list(args)]
    parse_json = output_format.lower() == "json"
    if parse_json and not _has_output_flag(args):
        cmd.extend(["-o", "json"])

    logger.info("Running: %s", " ".join(shlex.quote(p) for p in cmd))
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=TIMEWEB_CLI_TIMEOUT,
        cwd=cwd or None,
    )

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    if proc.returncode != 0:
        raise RuntimeError(
            "Command failed with non-zero exit code: "
            f"{proc.returncode}. stderr={stderr or '<empty>'} stdout={stdout or '<empty>'}"
        )

    result: dict[str, Any] = {
        "command": cmd,
        "cwd": cwd or str(Path.cwd()),
        "exit_code": proc.returncode,
        "stderr": stderr,
    }

    if parse_json:
        if not stdout:
            result["data"] = {}
            return result
        try:
            result["data"] = json.loads(stdout)
        except json.JSONDecodeError:
            result["data"] = None
            result["stdout"] = stdout
            result["note"] = "Output is not valid JSON."
        return result

    result["stdout"] = stdout
    return result


def _normalize_args(args: Sequence[str]) -> list[str]:
    normalized = [str(x).strip() for x in args if str(x).strip()]
    if not normalized:
        raise ValueError("args must contain at least one CLI token")
    if normalized[0].lower() == TIMEWEB_CLI_CMD.lower():
        normalized = normalized[1:]
    if not normalized:
        raise ValueError("args cannot contain only the CLI executable name")
    return normalized


@mcp.tool(name="timeweb_run_cli")
def timeweb_run_cli(
    args: list[str],
    output_format: str = "json",
    cwd: str = "",
) -> dict[str, Any]:
    """Run any twc command, e.g. args=['apps','create','./timeweb-app.yaml'].

    output_format: json|yaml|raw|default
    cwd: optional working directory where command should run
    """
    normalized_args = _normalize_args(args)
    output_format = output_format.lower().strip() or "json"
    if output_format not in {"json", "yaml", "raw", "default"}:
        raise ValueError("output_format must be one of: json, yaml, raw, default")

    if output_format != "json" and not _has_output_flag(normalized_args):
        normalized_args = [*normalized_args, "-o", output_format]

    command_cwd = cwd.strip() or None
    if command_cwd and not Path(command_cwd).exists():
        raise ValueError(f"cwd does not exist: {command_cwd}")

    return run_twc(normalized_args, output_format=output_format, cwd=command_cwd)


@mcp.tool(name="timeweb_account_status")
def timeweb_account_status() -> dict[str, Any]:
    """Return Timeweb account status for the current authenticated profile."""
    return run_twc(["account", "status"])


@mcp.tool(name="timeweb_whoami")
def timeweb_whoami() -> dict[str, Any]:
    """Show current CLI identity and authentication context."""
    return run_twc(["whoami"])


@mcp.tool(name="timeweb_list_servers")
def timeweb_list_servers(filter_expr: str = "") -> dict[str, Any]:
    """List cloud servers. filter_expr example: 'name:my-server' or 'status:on'."""
    args = ["server", "list"]
    if filter_expr.strip():
        args.extend(["-f", filter_expr.strip()])
    return run_twc(args)


@mcp.tool(name="timeweb_get_server")
def timeweb_get_server(server_id: str) -> dict[str, Any]:
    """Get details for a server by ID."""
    if not server_id.strip():
        raise ValueError("server_id is required")
    return run_twc(["server", "get", server_id.strip()])


@mcp.tool(name="timeweb_start_server")
def timeweb_start_server(server_ids: list[str]) -> dict[str, Any]:
    """Start one or more servers. Pass server_ids as a list."""
    ids = [s.strip() for s in server_ids if s.strip()]
    if not ids:
        raise ValueError("server_ids is required")
    return run_twc(["server", "boot", *ids])


@mcp.tool(name="timeweb_stop_server")
def timeweb_stop_server(server_ids: list[str], hard: bool = False) -> dict[str, Any]:
    """Stop one or more servers. Set hard=true for hard shutdown."""
    ids = [s.strip() for s in server_ids if s.strip()]
    if not ids:
        raise ValueError("server_ids is required")
    args = ["server", "shutdown", *ids]
    if hard:
        args.append("--hard")
    return run_twc(args)


@mcp.tool(name="timeweb_reboot_server")
def timeweb_reboot_server(server_ids: list[str], hard: bool = False) -> dict[str, Any]:
    """Reboot one or more servers. Set hard=true for hard reboot."""
    ids = [s.strip() for s in server_ids if s.strip()]
    if not ids:
        raise ValueError("server_ids is required")
    args = ["server", "reboot", *ids]
    if hard:
        args.append("--hard")
    return run_twc(args)


@mcp.tool(name="timeweb_list_apps")
def timeweb_list_apps(filter_expr: str = "") -> dict[str, Any]:
    """List App Platform applications. filter_expr example: 'name:backend'."""
    args = ["apps", "list"]
    if filter_expr.strip():
        args.extend(["-f", filter_expr.strip()])
    return run_twc(args)


@mcp.tool(name="timeweb_get_app")
def timeweb_get_app(app_id: str, wait_started: bool = False) -> dict[str, Any]:
    """Get app details. Set wait_started=true to return when app status becomes started."""
    app_id = app_id.strip()
    if not app_id:
        raise ValueError("app_id is required")
    args = ["apps", "get", app_id]
    if wait_started:
        args.append("--status")
    return run_twc(args)


@mcp.tool(name="timeweb_create_app")
def timeweb_create_app(config_path: str, wait_started: bool = True) -> dict[str, Any]:
    """Create a new app from YAML config path."""
    config_path = config_path.strip()
    if not config_path:
        raise ValueError("config_path is required")
    resolved = Path(config_path).expanduser()
    if not resolved.is_absolute():
        resolved = (Path.cwd() / resolved).resolve()
    if not resolved.exists():
        raise ValueError(f"config_path does not exist: {resolved}")

    args = ["apps", "create", str(resolved)]
    if wait_started:
        args.append("--status")
    return run_twc(args)


def main() -> int:
    logger.info("Starting Timeweb MCP server (stdio)")
    logger.info("Using env file: %s", ENV_FILE)
    logger.info("Using CLI command: %s", TIMEWEB_CLI_CMD)
    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
