# dfs_client_lib.py

import socket
import json
import os
import time
import uuid

MASTER_HOST = "127.0.0.1"
MASTER_PORT = 5000

# This uniquely identifies this client process (GUI or CLI instance)
CLIENT_ID = str(uuid.uuid4())


def send_json(conn, obj):
    conn.sendall(json.dumps(obj).encode())


def recv_json(conn):
    data = conn.recv(4096).decode()
    if not data:
        raise ConnectionError("No data from server")
    return json.loads(data)


def send_to_master(message: dict) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((MASTER_HOST, MASTER_PORT))
        send_json(s, message)
        resp = recv_json(s)
    return resp


def parse_addr(addr_str):
    host, port_str = addr_str.split(":")
    return host, int(port_str)


# ---------- High-level API ----------

def list_files():
    """Ask master for list of all known files in DFS."""
    req = {"type": "LIST_FILES"}
    return send_to_master(req)
def get_file_info(filename: str):
    filename = os.path.basename(filename)
    return send_to_master({"type": "FILE_INFO", "filename": filename})



def get_nodes_status():
    """Ask master for status (ALIVE/DEAD) of all nodes."""
    req = {"type": "NODES_STATUS"}
    return send_to_master(req)


def upload_file(filepath: str):
    """
    Upload file to DFS with replication and write-locking.

    Steps:
      1. Check file exists locally.
      2. Acquire write lock from master.
      3. Ask master where to upload.
      4. Upload to each node.
      5. Inform master (UPLOAD_DONE).
      6. Release write lock.
    """
    if not os.path.exists(filepath):
        return {"status": "error", "message": f"File {filepath} not found"}

    filename = os.path.basename(filepath)   # DFS filename
    filesize = os.path.getsize(filepath)

    # 1 & 2. Acquire lock for this filename
    lock_resp = send_to_master({
        "type": "LOCK_REQUEST",
        "filename": filename,
        "client_id": CLIENT_ID
    })
    if lock_resp.get("status") != "ok":
        # lock_resp["status"] will be "locked" in that case
        return {
            "status": "error",
            "message": lock_resp.get("message", f"File '{filename}' is locked")
        }

    # Hold lock for a while so concurrent clients can collide (demo critical section)
    time.sleep(10)

    try:
        # 3. Ask master for nodes
        resp = send_to_master({"type": "UPLOAD_REQUEST", "filename": filename})
        nodes = resp.get("nodes", [])
        if not nodes:
            return {"status": "error", "message": "No nodes available for upload"}

        # 4. Upload to each node
        with open(filepath, "rb") as f:
            file_data = f.read()

        for addr_str in nodes:
            host, port = parse_addr(addr_str)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, port))
                    header = {
                        "type": "UPLOAD_FILE",
                        "filename": filename,
                        "size": filesize,
                    }
                    send_json(s, header)
                    ready = recv_json(s)
                    if ready.get("status") != "ready":
                        return {"status": "error", "message": f"Node {addr_str} not ready"}
                    s.sendall(file_data)
            except Exception as e:
                return {"status": "error", "message": f"Upload to {addr_str} failed: {e}"}

        # 5. Inform master
        done_resp = send_to_master({
            "type": "UPLOAD_DONE",
            "filename": filename,
            "nodes": nodes
        })

        if done_resp.get("status") == "ok":
            return {"status": "ok", "message": f"Uploaded {filename} to {len(nodes)} nodes"}
        else:
            return {"status": "error", "message": "Master failed to register upload"}

    finally:
        # 6. Always try to release lock (even if upload failed midway)
        try:
            send_to_master({
                "type": "LOCK_RELEASE",
                "filename": filename,
                "client_id": CLIENT_ID
            })
        except Exception:
            # If master is down, just ignore here
            pass


def download_file(filename: str, save_as: str = None):
    """
    Download file from DFS.
      1. Ask master for alive replicas.
      2. Download from the first available node.

    NOTE: We always use os.path.basename(filename) as DFS key,
    so passing a full path still works.
    """
    dfs_name = os.path.basename(filename)  # normalize to DFS filename

    # 1. Ask master
    resp = send_to_master({"type": "DOWNLOAD_REQUEST", "filename": dfs_name})
    if resp.get("status") != "ok":
        return {"status": "error", "message": resp.get("message", "Download failed")}

    nodes = resp.get("nodes", [])
    if not nodes:
        return {"status": "error", "message": "No alive replicas returned by master"}

    target_addr = nodes[0]
    host, port = parse_addr(target_addr)

    # 2. Ask node for file
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            header = {"type": "DOWNLOAD_FILE", "filename": dfs_name}
            send_json(s, header)
            info = recv_json(s)

            if info.get("status") != "ok":
                return {"status": "error", "message": info.get("message", "Node error")}

            size = info.get("size")
            remaining = size
            chunks = []

            while remaining > 0:
                chunk = s.recv(min(4096, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)

        data = b"".join(chunks)

    except Exception as e:
        return {"status": "error", "message": f"Failed to download from {target_addr}: {e}"}

    # 3. Save to disk
    if save_as is None:
        save_as = dfs_name  # default to DFS filename

    with open(save_as, "wb") as f:
        f.write(data)

    return {"status": "ok", "message": f"Downloaded {dfs_name} from {target_addr} -> {save_as}"}


def delete_file(filename: str):
    """
    Delete a file from all replicas:
      1. Ask master (DOWNLOAD_REQUEST) to get list of node addresses.
      2. Send DELETE_FILE to each node.
      3. Inform master with DELETE_DONE.

    NOTE: We normalize filename to basename so callers can pass full paths.
    """
    dfs_name = os.path.basename(filename)

    # 1. Get list of nodes holding this file
    resp = send_to_master({"type": "DOWNLOAD_REQUEST", "filename": dfs_name})
    if resp.get("status") != "ok":
        return {"status": "error", "message": resp.get("message", "File not found")}

    nodes = resp.get("nodes", [])

    # 2. Delete on each node
    for addr_str in nodes:
        host, port = parse_addr(addr_str)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                header = {"type": "DELETE_FILE", "filename": dfs_name}
                send_json(s, header)
                _ = recv_json(s)  # ignore details for now
        except Exception as e:
            print(f"[CLIENT] Delete on {addr_str} failed: {e}")

    # 3. Inform master
    done_resp = send_to_master({"type": "DELETE_DONE", "filename": dfs_name})
    if done_resp.get("status") == "ok":
        return {"status": "ok", "message": f"Deleted {dfs_name} from DFS"}
    else:
        return {"status": "error", "message": "Master failed to remove metadata"}
