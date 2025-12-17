# dfs_client_gui.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

import dfs_client_lib as dfs  # our shared client library


class DFSClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Distributed File System Client")
        self.root.geometry("900x500")

        self.create_widgets()
        self.refresh_files()

    # ---------- UI Layout ----------

    def create_widgets(self):
        # Top frame: file selection & buttons
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_frame, text="Local file / DFS filename:").pack(side=tk.LEFT)

        self.filename_entry = ttk.Entry(top_frame, width=50)
        self.filename_entry.pack(side=tk.LEFT, padx=5)

        browse_btn = ttk.Button(top_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=5)

        # Button frame
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(side=tk.TOP, fill=tk.X)

        upload_btn = ttk.Button(btn_frame, text="Upload", command=self.on_upload)
        upload_btn.pack(side=tk.LEFT, padx=5)

        download_btn = ttk.Button(btn_frame, text="Download", command=self.on_download)
        download_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = ttk.Button(btn_frame, text="Delete", command=self.on_delete)
        delete_btn.pack(side=tk.LEFT, padx=5)
        details_btn = ttk.Button(btn_frame, text="File Details", command=self.on_file_details)
        details_btn.pack(side=tk.LEFT, padx=5)


        list_btn = ttk.Button(btn_frame, text="Refresh Files", command=self.on_list_files)
        list_btn.pack(side=tk.LEFT, padx=5)

        nodes_btn = ttk.Button(btn_frame, text="Nodes Status", command=self.on_nodes_status)
        nodes_btn.pack(side=tk.LEFT, padx=5)

        # Middle: DFS files list
        middle_frame = ttk.LabelFrame(self.root, text="Files in DFS", padding=10)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.files_listbox = tk.Listbox(middle_frame)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=scrollbar.set)

        # Right: logs + node status
        right_frame = ttk.Frame(self.root, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(right_frame, text="Logs", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        nodes_frame = ttk.LabelFrame(right_frame, text="Nodes Status", padding=5)
        nodes_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.nodes_text = tk.Text(nodes_frame, height=6, wrap=tk.WORD)
        self.nodes_text.pack(fill=tk.BOTH, expand=True)

    # ---------- Utility ----------

    def browse_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.insert(0, filepath)

    def log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def set_nodes_status(self, text: str):
        self.nodes_text.delete("1.0", tk.END)
        self.nodes_text.insert(tk.END, text)

    def run_in_thread(self, target, *args):
        t = threading.Thread(target=target, args=args)
        t.daemon = True
        t.start()
    

    def get_selected_filename(self):
        """If nothing typed, use selected from listbox."""
        name = self.filename_entry.get().strip()
        if not name:
            sel = self.files_listbox.curselection()
            if sel:
                name = self.files_listbox.get(sel[0])
        return name

    # ---------- Button handlers ----------

    def on_file_details(self):
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a file from DFS list.")
            return

        filename = self.files_listbox.get(selection[0])
        self.log(f"[DETAILS] Getting info for {filename}...")
        self.run_in_thread(self._file_details_worker, filename)


    def _file_details_worker(self, filename):
        try:
            resp = dfs.get_file_info(filename)
            if resp.get("status") != "ok":
                self.log("[DETAILS] Error: " + resp.get("message"))
                return

            replicas = resp.get("replicas", [])
            self.log(f"[DETAILS] File: {filename}")
            for r in replicas:
                nid = r["node_id"]
                addr = r["address"]
                alive = "ALIVE" if r["alive"] else "DEAD"
                self.log(f"  - {nid} @ {addr} [{alive}]")

        except Exception as e:
            self.log(f"[DETAILS] Error: {e}")


    def on_upload(self):
        path = self.filename_entry.get().strip()
        if not path:
            messagebox.showwarning("Warning", "Select or type a local file path to upload.")
            return
        self.log(f"[UPLOAD] Starting upload: {path}")
        self.run_in_thread(self._upload_worker, path)

    def _upload_worker(self, path):
        resp = dfs.upload_file(path)
        self.log("[UPLOAD] " + resp.get("message", str(resp)))
        self.refresh_files()

    def on_download(self):
        filename = self.get_selected_filename()
        if not filename:
            messagebox.showwarning("Warning", "Select a DFS file or type its name.")
            return

        save_as = filedialog.asksaveasfilename(initialfile=filename)
        if not save_as:
            return

        self.log(f"[DOWNLOAD] Downloading {filename} -> {save_as}")
        self.run_in_thread(self._download_worker, filename, save_as)

    def _download_worker(self, filename, save_as):
        resp = dfs.download_file(filename, save_as=save_as)
        self.log("[DOWNLOAD] " + resp.get("message", str(resp)))

    def on_delete(self):
        filename = self.get_selected_filename()
        if not filename:
            messagebox.showwarning("Warning", "Select a DFS file or type its name for deletion.")
            return

        if not messagebox.askyesno("Confirm", f"Delete '{filename}' from DFS?"):
            return

        self.log(f"[DELETE] Deleting {filename} from DFS")
        self.run_in_thread(self._delete_worker, filename)

    def _delete_worker(self, filename):
        resp = dfs.delete_file(filename)
        self.log("[DELETE] " + resp.get("message", str(resp)))
        self.refresh_files()

    def on_list_files(self):
        self.refresh_files()

    def refresh_files(self):
        self.log("[LIST] Refreshing files from master...")
        self.run_in_thread(self._list_files_worker)

    def _list_files_worker(self):
        resp = dfs.list_files()
        files = resp.get("files", [])
        self.files_listbox.delete(0, tk.END)
        for f in files:
            self.files_listbox.insert(tk.END, f)
        self.log(f"[LIST] {len(files)} file(s) in DFS.")

    def on_nodes_status(self):
        self.log("[NODES] Refreshing node status...")
        self.run_in_thread(self._nodes_status_worker)

    def _nodes_status_worker(self):
        resp = dfs.get_nodes_status()
        nodes = resp.get("nodes", [])
        lines = []
        for n in nodes:
            lines.append(f"{n['id']} @ {n['address']} [{n['status']}]")
        status_text = "\n".join(lines) if lines else "No nodes registered."
        self.set_nodes_status(status_text)
        self.log("[NODES] Status updated.")


if __name__ == "__main__":
    root = tk.Tk()
    app = DFSClientGUI(root)
    root.mainloop()
