"""Minimal UDP receiver for testing Forza telemetry on 127.0.0.1:1050

Prints packet counts and lengths and a short hex dump for the first few packets.
"""
import socket
import binascii

HOST = "127.0.0.1"
PORT = 1050

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    # Best-effort: set SO_REUSEADDR before bind to reduce "address in use" on quick restarts
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass
    sock.bind((HOST, PORT))
except Exception as exc:
    print(f"Failed to bind {HOST}:{PORT}: {exc}")
    # Try a fallback: bind to 0.0.0.0 so we receive packets sent to any local address
    try:
        print(f"Attempting fallback bind to 0.0.0.0:{PORT}")
        sock.bind(("0.0.0.0", PORT))
        print(f"Fallback bind succeeded: 0.0.0.0:{PORT}")
    except Exception as exc2:
        print(f"Fallback bind failed: {exc2}")
        # Attempt to provide netstat output to help identify the owning process (Windows)
        try:
            import subprocess

            print("--- netstat -aon (filtered for :1050) ---")
            p = subprocess.run(["netstat", "-aon"], capture_output=True, text=True)
            for line in p.stdout.splitlines():
                if ":%d" % PORT in line:
                    print(line)
        except Exception:
            pass
        raise

print(f"Test receiver bound to {HOST}:{PORT}. Waiting for packets...")
count = 0
try:
    while True:
        data, addr = sock.recvfrom(8192)
        count += 1
        print(f"Packet #{count} Length={len(data)} bytes from {addr[0]}:{addr[1]}")
        if count <= 8:
            print(binascii.hexlify(data[:128]).upper().decode('ascii'))
except KeyboardInterrupt:
    print('\nStopped by user')
finally:
    sock.close()
