"""Master Server for Distributed File System

Coordinates storage nodes, tracks file metadata and replication, and
handles client requests for upload/download, locks, and node status.

Configuration:
- MASTER_HOST / MASTER_PORT: listening address
- REPLICATION_FACTOR: number of replicas per file
- HEARTBEAT_TIMEOUT: seconds after which a node is considered dead
"""

import socket
import threading
import json
import time

MASTER_HOST = "127.0.0.1"
MASTER_PORT = 5000

# Number of replicas per file
REPLICATION_FACTOR = 2

# Seconds without heartbeat to mark node dead
HEARTBEAT_TIMEOUT = 10

# node_id -> {"addr": "host:port", "last_heartbeat": t, "alive": bool}
nodes = {}

# filename -> ["host:port", "host:port", ...]
file_table = {}

# filename -> client_id (who currently holds the write lock)
file_locks = {}

lock = threading.Lock()


def recv_json(conn):
    data = conn.recv(4096).decode()
    return json.loads(data)


def send_json(conn, obj):
    conn.sendall(json.dumps(obj).encode())


def choose_nodes():
    """Pick nodes (by id) for replication."""
    alive_nodes = [nid for nid in nodes if nodes[nid]["alive"]]
    return alive_nodes[:REPLICATION_FACTOR]


def handle_client(conn, addr):
    try:
        msg = recv_json(conn)
    except Exception:
        conn.close()
        return

    mtype = msg.get("type")

    # ---------- NODE side messages ----------
    if mtype == "REGISTER_NODE":
        node_id = msg["node_id"]
        with lock:
            nodes[node_id] = {
                "addr": msg["addr"],
                "last_heartbeat": time.time(),
                "alive": True
            }
        print(f"[MASTER] Node registered: {node_id} @ {msg['addr']}")
        send_json(conn, {"status": "ok"})
        conn.close()
        return

    if mtype == "HEARTBEAT":
        nid = msg["node_id"]
        with lock:
            if nid in nodes:
                nodes[nid]["last_heartbeat"] = time.time()
                nodes[nid]["alive"] = True
        send_json(conn, {"status": "ok"})
        conn.close()
        return

    # ---------- LOCK management (from clients) ----------
    if mtype == "LOCK_REQUEST":
        filename = msg["filename"]
        client_id = msg.get("client_id")
        with lock:
            owner = file_locks.get(filename)
            if owner is None or owner == client_id:
                # grant lock
                file_locks[filename] = client_id
                send_json(conn, {"status": "ok", "message": "Lock granted"})
            else:
                send_json(conn, {
                    "status": "locked",
                    "message": f"File '{filename}' is currently locked by another client."
                })
        conn.close()
        return

    if mtype == "LOCK_RELEASE":
        filename = msg["filename"]
        client_id = msg.get("client_id")
        with lock:
            owner = file_locks.get(filename)
            if owner == client_id:
                del file_locks[filename]
        send_json(conn, {"status": "ok"})
        conn.close()
        return

    # ---------- CLIENT side messages ----------
    if mtype == "LIST_FILES":
        with lock:
            send_json(conn, {"files": list(file_table.keys())})

    elif mtype == "NODES_STATUS":
        resp = []
        with lock:
            for nid, info in nodes.items():
                resp.append({
                    "id": nid,
                    "address": info["addr"],
                    "status": "ALIVE" if info["alive"] else "DEAD"
                })
        send_json(conn, {"nodes": resp})

    elif mtype == "UPLOAD_REQUEST":
        filename = msg["filename"]
        with lock:
            chosen_ids = choose_nodes()
            chosen_addrs = [nodes[n]["addr"] for n in chosen_ids]
        send_json(conn, {"nodes": chosen_addrs})

    elif mtype == "UPLOAD_DONE":
        filename = msg["filename"]
        node_addrs = msg["nodes"]  # list of "host:port"
        with lock:
            file_table[filename] = node_addrs
        send_json(conn, {"status": "ok"})

    elif mtype == "DOWNLOAD_REQUEST":
        filename = msg["filename"]
        with lock:
            if filename not in file_table:
                send_json(conn, {"status": "error", "message": "File not found"})
                conn.close()
                return
            addr_list = file_table[filename][:]

            # Filter only addresses whose nodes are alive (if possible)
            alive_addrs = []
            for addr_str in addr_list:
                for nid, info in nodes.items():
                    if info["addr"] == addr_str and info["alive"]:
                        alive_addrs.append(addr_str)
                        break

        if not alive_addrs:
            send_json(conn, {"status": "error", "message": "No alive replicas"})
        else:
            send_json(conn, {"status": "ok", "nodes": alive_addrs})
    elif mtype == "FILE_INFO":
        filename = msg["filename"]
        with lock:
            if filename not in file_table:
                send_json(conn, {"status": "error", "message": "File not found"})
                conn.close()
                return

            addr_list = file_table[filename][:]

            replicas = []
            for addr_str in addr_list:
                is_alive = False
                node_name = None

                for nid, info in nodes.items():
                    if info["addr"] == addr_str:
                        node_name = nid
                        is_alive = info["alive"]
                        break

                replicas.append({
                    "node_id": node_name,
                    "address": addr_str,
                    "alive": is_alive
                })

        send_json(conn, {"status": "ok", "replicas": replicas})
        conn.close()
        return


    elif mtype == "DELETE_DONE":
        filename = msg["filename"]
        with lock:
            if filename in file_table:
                del file_table[filename]
        send_json(conn, {"status": "ok"})

    conn.close()


def heartbeat_monitor():
    while True:
        time.sleep(2)
        now = time.time()
        with lock:
            for nid in nodes:
                if now - nodes[nid]["last_heartbeat"] > HEARTBEAT_TIMEOUT:
                    if nodes[nid]["alive"]:
                        nodes[nid]["alive"] = False
                        print(f"[MASTER] Node {nid} is DEAD")


def start_master():
    threading.Thread(target=heartbeat_monitor, daemon=True).start()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((MASTER_HOST, MASTER_PORT))
    server.listen()

    print(f"[MASTER] Running on {MASTER_HOST}:{MASTER_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    start_master()
