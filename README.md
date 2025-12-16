# Distributed File System

A simple distributed file system prototype with a master server coordinating multiple storage nodes and client interfaces (CLI + GUI).

## Components
- `master_server.py`: Coordinates storage nodes, tracks file metadata, handles replication.
- `storage_node.py`: Node process handling file storage operations (put/get/delete).
- `dfs_client_lib.py`: Client library for interacting with the master + nodes.
 - See `CONFIG.md` for configuration details and `.env.example` for environment overrides.
- `dfs_client_cli.py`: Command-line client built on `dfs_client_lib.py`.
- `dfs_client_gui.py`: Basic GUI client.

## Quick Start
1. Start the master server:
   python master_server.py
   ```
2. Start storage nodes (adjust ports/paths as needed):
   python storage_node.py --node-id 1 --port 5001
   python storage_node.py --node-id 2 --port 5002
   python storage_node.py --node-id 3 --port 5003
   ```
3. Use the CLI client:
   ```bash
 - Or use the example script: `examples/quickstart.ps1`.
   python dfs_client_cli.py put ./path/to/file.txt /remote/file.txt
   python dfs_client_cli.py get /remote/file.txt ./downloads/file.txt
   ```

## Notes
- Local node folders like `storage_node1/`, `storage_node2/`, `storage_node3/` are ignored by Git.
- Configure replication and node discovery in `master_server.py`.
- For Windows PowerShell, use `python` from your active environment.

## Windows Setup
- Install Python 3.10+ and ensure `python` is on PATH.
- (Optional) Create venv:
   ```powershell
   python -m venv .venv; .\.venv\Scripts\Activate.ps1
   ```
- Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
- Run services as separate terminals in PowerShell:
   ```powershell
   python master_server.py
   python storage_node.py --node-id 1 --port 5001
   python storage_node.py --node-id 2 --port 5002
   python storage_node.py --node-id 3 --port 5003
   ```

## Dependencies
See `requirements.txt` for Python packages used.

## CLI Usage
See `USAGE_CLI.md` for common commands and examples.

## Dashboard
See `USAGE_DASHBOARD.md` for dashboard usage and features.

## Troubleshooting
See `TROUBLESHOOTING.md` for common issues and fixes.

## Roadmap
- Add health checks and automatic rebalancing.
- Improve GUI and dashboard.
- Persist metadata to a lightweight DB.
