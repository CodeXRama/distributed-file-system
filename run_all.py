import subprocess
import os
import time

# 🔴 IMPORTANT: This must match your actual project folder
PROJECT_PATH = r"C:\Users\Admin\Desktop\Distributed_file_system"

# Windows flag: open in a new console window
CREATE_NEW_CONSOLE = 0x00000010

def open_terminal(title: str, command: str):
    """
    Open a new cmd.exe window with the given title and run the command.
    We set cwd=PROJECT_PATH so we don't need 'cd' inside the command.
    """
    inner_cmd = f'title {title} && {command}'
    subprocess.Popen(
        ["cmd.exe", "/k", inner_cmd],
        cwd=PROJECT_PATH,
        creationflags=CREATE_NEW_CONSOLE
    )

def main():
    if not os.path.isdir(PROJECT_PATH):
        print("ERROR: PROJECT_PATH does not exist:")
        print(PROJECT_PATH)
        return

    print("Launching Distributed File System...")

    # MASTER
    open_terminal("MASTER SERVER", "python master_server.py")
    time.sleep(1)

    # NODES
    open_terminal("NODE 1", "python storage_node.py node1 6001")
    open_terminal("NODE 2", "python storage_node.py node2 6002")
    open_terminal("NODE 3", "python storage_node.py node3 6003")
    time.sleep(1)

    # CLIENT GUI WINDOWS
    open_terminal("CLIENT GUI 1", "python dfs_client_gui.py")
    open_terminal("CLIENT GUI 2", "python dfs_client_gui.py")

    print("All components launched. Check the new cmd windows.")

if __name__ == "__main__":
    main()
