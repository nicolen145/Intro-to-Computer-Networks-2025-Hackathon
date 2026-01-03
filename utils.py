import socket

# TCP Receive Utility

# This file provides a helper function for safely receiving data over TCP.
# Since TCP is stream-based, recv() may return fewer bytes than requested,
# so this function ensures that exactly n bytes are read or an error is raised.


def recv_exact(sock: socket.socket, n: int) -> bytes:
    # Receives exactly n bytes from a TCP socket or raises an error if the connection is closed;
    chunks = []
    got = 0
    while got < n:
        part = sock.recv(n - got)
        if not part:
            raise ConnectionError("socket closed")
        chunks.append(part)
        got += len(part)
    return b"".join(chunks)
