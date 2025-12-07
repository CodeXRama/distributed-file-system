# Quickstart script for Windows PowerShell
# Start master and three nodes in separate windows (manually run each line in its own terminal)
# Requires dependencies from requirements.txt installed

python master_server.py
python storage_node.py --node-id 1 --port 5001
python storage_node.py --node-id 2 --port 5002
python storage_node.py --node-id 3 --port 5003
