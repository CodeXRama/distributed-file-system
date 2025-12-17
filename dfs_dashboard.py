# dfs_dashboard.py
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import threading
import time

import dfs_client_lib as dfs  # reuse your existing client lib

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

class DFSDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("DFS Control Panel & Dashboard")
        self.root.geometry("700x400")

        # Process handles
        self.master_proc = None
        self.node_procs = []
        self.client_procs = []

        self.create_widgets()

    # ---------- UI ----------
    def create_widgets(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        start_btn = ttk.Button(top_frame, text="Start System", command=self.on_start_system)
        start_btn.pack(side=tk.LEFT, padx=5)

        stop_btn = ttk.Button(top_frame, text="Stop System", command=self.on_stop_system)
        stop_btn.pack(side=tk.LEFT, padx=5)

        client_btn = ttk.Button(top_frame, text="Start Extra Client", command=self.on_start_client)
        client_btn.pack(side=tk.LEFT, padx=5)

        status_btn = ttk.Button(top_frame, text="Refresh Node Status", command=self.on_refresh_nodes)
        status_btn.pack(side=tk.LEFT, padx=5)

        # Node status panel
        nodes_frame = ttk.LabelFrame(self.root, text="Node Status", padding=10)
        nodes_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.nodes_text = tk.Text(nodes_frame, height=10, wrap=tk.WORD)
        self.nodes_text.pack(fill=tk.BOTH, expand=True)

        # Log panel
        log_frame = ttk.LabelFrame(self.root, text="Dashboard Log", padding=10)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def set_nodes_status(self, text: str):
        self.nodes_text.delete("1.0", tk.END)
        self.nodes_text.insert(tk.END, text)

    # ---------- Process control ----------
    def start_process(self, title, cmd_args):
        """
        Start a Python process in the background (no extra console window).
        """
        self.log(f"Starting {title}...")
        proc = subprocess.Popen(
            ["python"] + cmd_args,
            cwd=PROJECT_PATH,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc

    def on_start_system(self):
        if self.master_proc is not None:
            messagebox.showinfo("Info", "System already running.")
            return

        try:
            # Start master
            self.master_proc = self.start_process("MASTER SERVER", ["master_server.py"])
            time.sleep(0.5)

            # Start nodes
            self.node_procs = []
            self.node_procs.append(self.start_process("NODE 1", ["storage_node.py", "node1", "6001"]))
            self.node_procs.append(self.start_process("NODE 2", ["storage_node.py", "node2", "6002"]))
            self.node_procs.append(self.start_process("NODE 3", ["storage_node.py", "node3", "6003"]))

            time.sleep(1.0)

            # Start one client GUI
            self.client_procs = []
            self.client_procs.append(self.start_process("CLIENT GUI 1", ["dfs_client_gui.py"]))

            self.log("DFS system started.")
        except Exception as e:
            self.log(f"[ERROR] Failed to start system: {e}")
            messagebox.showerror("Error", f"Failed to start system: {e}")

    def on_stop_system(self):
        # Stop clients
        for p in self.client_procs:
            try:
                p.terminate()
            except Exception:
                pass
        self.client_procs = []

        # Stop nodes
        for p in self.node_procs:
            try:
                p.terminate()
            except Exception:
                pass
        self.node_procs = []

        # Stop master
        if self.master_proc is not None:
            try:
                self.master_proc.terminate()
            except Exception:
                pass
            self.master_proc = None

        self.log("DFS system stopped.")

    def on_start_client(self):
        if self.master_proc is None:
            messagebox.showwarning("Warning", "Start the system first.")
            return
        try:
            p = self.start_process(f"CLIENT GUI {len(self.client_procs)+1}", ["dfs_client_gui.py"])
            self.client_procs.append(p)
            self.log("Started extra client GUI.")
        except Exception as e:
            self.log(f"[ERROR] Failed to start client: {e}")

    # ---------- Node status ----------
    def on_refresh_nodes(self):
        def worker():
            try:
                resp = dfs.get_nodes_status()
                nodes = resp.get("nodes", [])
                lines = []
                for n in nodes:
                    lines.append(f"{n['id']} @ {n['address']} [{n['status']}]")
                status_text = "\n".join(lines) if lines else "No nodes registered."
                self.set_nodes_status(status_text)
                self.log("Node status refreshed.")
            except Exception as e:
                self.log(f"[ERROR] Cannot get node status: {e}")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = DFSDashboard(root)
    root.mainloop()
