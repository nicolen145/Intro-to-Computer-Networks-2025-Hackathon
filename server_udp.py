import socket
import threading
import time
from protocol import pack_offer

# UDP Offer Broadcaster

# This file handles periodic UDP broadcast of server offers.
# The server advertises its availability so clients can discover it automatically.
# Broadcasting runs in a separate thread and stops cleanly using a threading.Event.


def start_udp_broadcaster(tcp_port: int, server_name: str, stop_event: threading.Event,
                          udp_port: int = 13122, interval_sec: float = 1.0):
    # Periodically broadcasts an offer message over UDP until stop_event is set;
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    offer = pack_offer(tcp_port, server_name)  # Pre-pack the offer message once;

    while not stop_event.is_set():
        try:
            s.sendto(offer, ("<broadcast>", udp_port))  # Send offer to all clients via broadcast;
        except Exception:
            pass
        stop_event.wait(interval_sec)  # Sleep without busy-waiting;

    try:
        s.close()  # Close the socket when broadcasting stops;
    except Exception:
        pass
