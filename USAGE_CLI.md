# CLI Usage Guide

This guide shows common commands using the CLI client `dfs_client_cli.py`.

## Upload a file
```powershell
python dfs_client_cli.py put .\local\file.txt /remote/path/file.txt
```

## Download a file
```powershell
python dfs_client_cli.py get /remote/path/file.txt .\downloads\file.txt
```

## List files in the DFS
```powershell
python dfs_client_cli.py ls
```

## Delete a file
```powershell
python dfs_client_cli.py rm /remote/path/file.txt
```

## Lock a file for writing
```powershell
python dfs_client_cli.py lock /remote/path/file.txt --client-id client1
```

## Release a lock
```powershell
python dfs_client_cli.py unlock /remote/path/file.txt --client-id client1
```

Notes:
- Paths starting with `/` are DFS paths managed by the master server.
- Local paths use Windows `\` separators.
