# Configuration Guide

This document describes configurable settings for the Distributed File System.

## Master Server
- `MASTER_HOST`: IP address to bind (default: `127.0.0.1`).
- `MASTER_PORT`: TCP port to listen (default: `5000`).
- `REPLICATION_FACTOR`: Number of replicas per file (default: `2`).
- `HEARTBEAT_TIMEOUT`: Seconds after last heartbeat to consider node dead (default: `10`).

## Storage Nodes
- `--node-id`: Unique identifier for the node (string or int).
- `--port`: Listening port for client transfers.
- `--root`: Optional local folder path for storing files.

## Environment Variables
You can set environment variables in `.env` to override defaults.

- `DFS_MASTER_HOST`
- `DFS_MASTER_PORT`
- `DFS_REPLICATION_FACTOR`
- `DFS_HEARTBEAT_TIMEOUT`

## Examples
See `examples/` for sample commands.
