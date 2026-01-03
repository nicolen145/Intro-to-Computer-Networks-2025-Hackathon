import threading
import socket

from server_tcp import start_tcp_server, accept_loop
from server_udp import start_udp_broadcaster

# Server Entry Point

# This file is the main entry point of the Blackjack server.
# It starts the TCP server, launches the UDP offer broadcaster,
# and accepts incoming client connections until shutdown.


SERVER_NAME = "Casino del TCP Dealer"   # Server team name advertised to clients;


def get_local_ip():
    # Determines the local IP address used to reach external networks;
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "0.0.0.0"
    finally:
        s.close()


def main():
    # Starts the TCP server, UDP broadcaster, and client accept loop;
    stop_event = threading.Event()

    tcp_sock, tcp_port = start_tcp_server(SERVER_NAME, host="", port=0)
    ip = get_local_ip()
    print(f"[SERVER] Server started, listening on IP address {ip}")

    # Start UDP broadcaster in a background thread;
    t_udp = threading.Thread(
        target=start_udp_broadcaster,
        args=(tcp_port, SERVER_NAME, stop_event),
        daemon=True
    )
    t_udp.start()
    print("[SERVER] Broadcasting offers via UDP every 1 second...")

    try:
        accept_loop(tcp_sock, SERVER_NAME, stop_event)
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        stop_event.set()
        try:
            tcp_sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
