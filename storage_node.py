# storage_node.py
import socket
import threading
import json
import time
import os
import sys

MASTER_HOST = "127.0.0.1"
MASTER_PORT = 5000
HEARTBEAT_INTERVAL = 3  # seconds

def send_json(conn, obj):
    data = json.dumps(obj).encode()
    conn.sendall(data)

def recv_json(conn):
    data = conn.recv(4096).decode()
    if not data:
        raise ConnectionError("No data received")
    return json.loads(data)

def send_to_master(msg):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((MASTER_HOST, MASTER_PORT))
        send_json(s, msg)
        try:
            resp = recv_json(s)
        except Exception:
            resp = {}
    return resp

class StorageNode:
    def __init__(self, node_id, host, port, storage_dir):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.storage_dir = storage_dir

        os.makedirs(self.storage_dir, exist_ok=True)

    # ---------- Master communication ----------

    def register_with_master(self):
        addr_str = f"{self.host}:{self.port}"
        msg = {
            "type": "REGISTER_NODE",
            "node_id": self.node_id,
            "addr": addr_str,
        }
        resp = send_to_master(msg)
        print(f"[NODE {self.node_id}] Registered with master: {resp}")

    def heartbeat_loop(self):
        while True:
            try:
                msg = {"type": "HEARTBEAT", "node_id": self.node_id}
                _ = send_to_master(msg)
            except Exception as e:
                print(f"[NODE {self.node_id}] Heartbeat failed: {e}")
            time.sleep(HEARTBEAT_INTERVAL)

    # ---------- File operations ----------

    def handle_upload(self, conn, header):
        filename = os.path.basename(header["filename"])
        dest_path = os.path.join(self.storage_dir, filename)

        # Acknowledge header so client can start sending file
        send_json(conn, {"status": "ready"})

        # Receive file bytes until we've read 'size' bytes
        filesize = header.get("size")
        if filesize is None:
            # fallback: read until connection closes (not ideal but okay)
            with open(dest_path, "wb") as f:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
        else:
            remaining = filesize
            with open(dest_path, "wb") as f:
                while remaining > 0:
                    chunk = conn.recv(min(4096, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)

        print(f"[NODE {self.node_id}] Stored file {filename} at {dest_path}")

    def handle_download(self, conn, header):
        filename = os.path.basename(header["filename"])
        src_path = os.path.join(self.storage_dir, filename)

        if not os.path.exists(src_path):
            send_json(conn, {"status": "error", "message": "File not found"})
            return

        filesize = os.path.getsize(src_path)
        # Send header with file size
        send_json(conn, {"status": "ok", "size": filesize})

        # Send file bytes
        with open(src_path, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                conn.sendall(chunk)

        print(f"[NODE {self.node_id}] Sent file {filename} (size {filesize} bytes)")

    def handle_delete(self, conn, header):
        filename = os.path.basename(header["filename"])
        path = os.path.join(self.storage_dir, filename)

        if os.path.exists(path):
            os.remove(path)
            send_json(conn, {"status": "ok", "message": "Deleted"})
            print(f"[NODE {self.node_id}] Deleted file {filename}")
        else:
            send_json(conn, {"status": "error", "message": "File not found"})

    # ---------- Server loop ----------

    def handle_connection(self, conn, addr):
        try:
            header = recv_json(conn)
            mtype = header.get("type")

            if mtype == "UPLOAD_FILE":
                self.handle_upload(conn, header)
            elif mtype == "DOWNLOAD_FILE":
                self.handle_download(conn, header)
            elif mtype == "DELETE_FILE":
                self.handle_delete(conn, header)
            else:
                print(f"[NODE {self.node_id}] Unknown message type from client: {mtype}")
        except Exception as e:
            print(f"[NODE {self.node_id}] Error handling connection from {addr}: {e}")
        finally:
            conn.close()

    def start_server(self):
        # Register and start heartbeat thread
        self.register_with_master()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

        # Start TCP server for client uploads/downloads
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()
        print(f"[NODE {self.node_id}] Listening on {self.host}:{self.port}, storage={self.storage_dir}")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_connection, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    """
    Usage:
        python storage_node.py <node_id> <port>

    Example:
        python storage_node.py node1 6001
        python storage_node.py node2 6002
    """
    if len(sys.argv) < 3:
        print("Usage: python storage_node.py <node_id> <port>")
        sys.exit(1)

    node_id = sys.argv[1]
    port = int(sys.argv[2])

    node = StorageNode(
        node_id=node_id,
        host="127.0.0.1",
        port=port,
        storage_dir=f"storage_{node_id}",
    )
    node.start_server()
