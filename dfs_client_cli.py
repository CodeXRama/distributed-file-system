# dfs_client_cli.py

import argparse
import dfs_client_lib as dfs

def cmd_list(args):
    resp = dfs.list_files()
    files = resp.get("files", [])
    print("Files in DFS:")
    for f in files:
        print("  -", f)

def cmd_status(args):
    resp = dfs.get_nodes_status()
    nodes = resp.get("nodes", [])
    print("Nodes status:")
    for n in nodes:
        print(f"  - {n['id']} @ {n['address']} [{n['status']}]")

def cmd_upload(args):
    resp = dfs.upload_file(args.path)
    print(resp.get("message", resp))

def cmd_download(args):
    resp = dfs.download_file(args.filename, save_as=args.output)
    print(resp.get("message", resp))

def cmd_delete(args):
    resp = dfs.delete_file(args.filename)
    print(resp.get("message", resp))

def main():
    parser = argparse.ArgumentParser(description="DFS Client CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="List files in DFS")
    p_list.set_defaults(func=cmd_list)

    # status
    p_status = subparsers.add_parser("status", help="Show nodes status")
    p_status.set_defaults(func=cmd_status)

    # upload
    p_upload = subparsers.add_parser("upload", help="Upload a file")
    p_upload.add_argument("path", help="Path to local file")
    p_upload.set_defaults(func=cmd_upload)

    # download
    p_download = subparsers.add_parser("download", help="Download a file")
    p_download.add_argument("filename", help="Filename in DFS")
    p_download.add_argument("-o", "--output", help="Save as (local path)", default=None)
    p_download.set_defaults(func=cmd_download)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a file from DFS")
    p_delete.add_argument("filename", help="Filename in DFS")
    p_delete.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
