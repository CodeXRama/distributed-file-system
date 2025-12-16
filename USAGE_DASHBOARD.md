# Dashboard Usage

`dfs_dashboard.py` provides a simple view of nodes and stored files.

## Start the dashboard
```powershell
python dfs_dashboard.py
```

## Features
- Shows node status (alive/dead) from the master server.
- Lists stored files and their replicas.
- Basic refresh to fetch latest state.

## Notes
- Ensure the master server and storage nodes are running first.
- Configure connection settings in the script if needed.
