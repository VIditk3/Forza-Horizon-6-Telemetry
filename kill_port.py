"""Helper to find processes owning a TCP/UDP port and optionally kill them.

Usage:
    python kill_port.py --port 1050
    python kill_port.py --port 1050 --yes   # force kill without prompt

This attempts to be safe: it lists the matching netstat lines and tasklist output
and asks for confirmation before calling taskkill (Windows) or kill (POSIX).
"""
import argparse
import os
import re
import subprocess
import sys


def find_pids_windows(port: int):
    p = subprocess.run(["netstat", "-aon"], capture_output=True, text=True)
    pids = []
    for line in p.stdout.splitlines():
        if f":{port}" in line:
            parts = line.split()
            if parts:
                pid = parts[-1]
                if pid.isdigit():
                    pids.append((pid, line.strip()))
    return pids


def tasklist_info_windows(pid: str):
    p = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
    return p.stdout.strip()


def kill_pid_windows(pid: str, force: bool = True):
    args = ["taskkill", "/PID", pid]
    if force:
        args.append("/F")
    return subprocess.run(args, capture_output=True, text=True)


def find_pids_unix(port: int):
    # Try lsof first
    try:
        p = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
        pids = []
        for line in p.stdout.splitlines()[1:]:
            cols = re.split(r"\s+", line.strip())
            if len(cols) >= 2:
                pid = cols[1]
                if pid.isdigit():
                    pids.append((pid, line.strip()))
        return pids
    except FileNotFoundError:
        return []


def kill_pid_unix(pid: str, force: bool = True):
    sig = "-9" if force else "-15"
    return subprocess.run(["kill", sig, pid], capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--yes", action="store_true", help="Don't prompt; kill all found PIDs")
    args = parser.parse_args()

    port = args.port
    print(f"Searching for processes using port {port}...")

    if os.name == "nt":
        pids = find_pids_windows(port)
        if not pids:
            print("No matching netstat lines found for port", port)
            return 0
        print("Found the following entries:")
        for pid, line in pids:
            print(f"PID={pid}  {line}")
            info = tasklist_info_windows(pid)
            print(info)
            print("-")

        if not args.yes:
            ans = input("Kill all listed PIDs? [y/N]: ")
            if ans.strip().lower() != "y":
                print("Aborting — no processes were killed.")
                return 0

        for pid, _ in pids:
            print(f"Killing PID {pid}...")
            res = kill_pid_windows(pid)
            print(res.stdout)
            if res.stderr:
                print(res.stderr, file=sys.stderr)
        print("Done.")
        return 0
    else:
        pids = find_pids_unix(port)
        if not pids:
            print("No processes found using port", port)
            return 0
        print("Found the following entries:")
        for pid, line in pids:
            print(f"PID={pid}  {line}")
        if not args.yes:
            ans = input("Kill all listed PIDs? [y/N]: ")
            if ans.strip().lower() != "y":
                print("Aborting — no processes were killed.")
                return 0
        for pid, _ in pids:
            print(f"Killing PID {pid}...")
            res = kill_pid_unix(pid)
            print(res.stdout)
            if res.stderr:
                print(res.stderr, file=sys.stderr)
        print("Done.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
