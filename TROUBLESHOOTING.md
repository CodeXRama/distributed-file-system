# Troubleshooting

Common issues and fixes when running the Distributed File System.

## Python not found
- Ensure Python 3.10+ is installed and `python` is in PATH.

## Ports already in use
- Change node ports in `run_all.py` or your launch commands.

## Nodes show as DEAD
- Verify node processes are running.
- Check network connectivity and firewall.
- Confirm heartbeat timeout matches expected frequency.

## Upload or download fails
- Check file paths (DFS uses `/remote/...`, local uses `\\`).
- Verify nodes configured with the correct root folders.

## Reset environment
- Stop all terminals.
- Clear local storage directories (`storage_node1/`, `storage_node2/`, `storage_node3/`).
- Restart master and nodes.
