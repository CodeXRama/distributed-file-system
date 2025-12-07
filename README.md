# Distributed File System

A simple distributed file system prototype with a master server coordinating multiple storage nodes and client interfaces (CLI + GUI).

## Components
- `master_server.py`: Coordinates storage nodes, tracks file metadata, handles replication.
- `storage_node.py`: Node process handling file storage operations (put/get/delete).
- `dfs_client_lib.py`: Client library for interacting with the master + nodes.
- `dfs_client_cli.py`: Command-line client built on `dfs_client_lib.py`.
- `dfs_client_gui.py`: Basic GUI client.
- `dfs_dashboard.py`: Lightweight dashboard to visualize nodes and files.
- `run_all.py`: Convenience script to start master and nodes.

## Quick Start
1. Start the master server:
   ```bash
   python master_server.py
   ```
2. Start storage nodes (adjust ports/paths as needed):
   ```bash
   python storage_node.py --node-id 1 --port 5001
   python storage_node.py --node-id 2 --port 5002
   python storage_node.py --node-id 3 --port 5003
   ```
3. Use the CLI client:
   ```bash
   python dfs_client_cli.py put ./path/to/file.txt /remote/file.txt
   python dfs_client_cli.py get /remote/file.txt ./downloads/file.txt
   ```

## Notes
- Local node folders like `storage_node1/`, `storage_node2/`, `storage_node3/` are ignored by Git.
- Configure replication and node discovery in `master_server.py`.
- For Windows PowerShell, use `python` from your active environment.

## Roadmap
- Add health checks and automatic rebalancing.
- Improve GUI and dashboard.
- Persist metadata to a lightweight DB.
