import socket
import threading

from protocol import (
    pack_server_payload, unpack_request, unpack_client_payload,
    REQUEST_SIZE, CLIENT_PAYLOAD_SIZE,
    RESULT_NOT_OVER, RESULT_WIN, RESULT_LOSS, RESULT_TIE
)
from cards import Deck, card_value
from utils import recv_exact

# TCP Server Game Logic

# This file implements the TCP server-side game logic.
# It handles client connections, runs multiple blackjack rounds per client,
# manages dealer/player turns, and sends game updates using the protocol layer.
# Each client is handled in a separate thread.



def decide_winner(player_total: int, dealer_total: int) -> int:
    # Determines the round result based on blackjack totals;
    if player_total > 21:
        return RESULT_LOSS
    if dealer_total > 21:
        return RESULT_WIN
    if player_total > dealer_total:
        return RESULT_WIN
    if dealer_total > player_total:
        return RESULT_LOSS
    return RESULT_TIE


def handle_client(conn: socket.socket, addr, server_name: str):
    # Handles a single client session including all requested rounds;
    conn.settimeout(300.0)
    try:
        # Read initial request from client;
        req = recv_exact(conn, REQUEST_SIZE)
        rounds, client_name = unpack_request(req)

        print(f"[SERVER] Client {client_name} connected from {addr}, requested {rounds} rounds")

        wins = losses = ties = 0

        for r in range(1, rounds + 1):
            print(f"\n[SERVER] Round {r}/{rounds} vs {client_name}")

            deck = Deck()  # Creates a fresh shuffled deck for each round;

            # Deal initial cards;
            player_cards = [deck.draw(), deck.draw()]
            dealer_cards = [deck.draw(), deck.draw()]
            player_total = sum(card_value(c) for c in player_cards)
            dealer_total = sum(card_value(c) for c in dealer_cards)

            # Send player's cards (visible);
            for c in player_cards:
                conn.sendall(pack_server_payload(RESULT_NOT_OVER, c.rank, c.suit))

            # Send dealer's first card and keep the second hidden;
            conn.sendall(pack_server_payload(RESULT_NOT_OVER, dealer_cards[0].rank, dealer_cards[0].suit))

            print(f"[SERVER] Player cards: {player_cards[0]}, {player_cards[1]} (total={player_total})")
            print(f"[SERVER] Dealer upcard: {dealer_cards[0]} (hidden card is dealt)")

            # Handle player turn;
            player_bust = False
            while True:
                if player_total > 21:
                    player_bust = True
                    break

                # Receive player decision;
                data = recv_exact(conn, CLIENT_PAYLOAD_SIZE)
                decision = unpack_client_payload(data)
                print(f"[SERVER] Player decision: {decision}")

                if decision == "Stand":
                    break

                # Player hits;
                newc = deck.draw()
                player_cards.append(newc)
                player_total += card_value(newc)
                conn.sendall(pack_server_payload(RESULT_NOT_OVER, newc.rank, newc.suit))
                print(f"[SERVER] Player hits: {newc} (total={player_total})")

            if player_total > 21:
                player_bust = True

            # Handle dealer turn;
            if player_bust:
                print("[SERVER] Player busts -> dealer wins")
                result = RESULT_LOSS
                losses += 1
                conn.sendall(pack_server_payload(result, 0, 0))
                continue

            # Reveal dealer's hidden card;
            conn.sendall(pack_server_payload(RESULT_NOT_OVER, dealer_cards[1].rank, dealer_cards[1].suit))
            print(f"[SERVER] Dealer reveals: {dealer_cards[1]} (dealer_total={dealer_total})")

            while dealer_total < 17:
                newc = deck.draw()
                dealer_cards.append(newc)
                dealer_total += card_value(newc)
                conn.sendall(pack_server_payload(RESULT_NOT_OVER, newc.rank, newc.suit))
                print(f"[SERVER] Dealer hits: {newc} (dealer_total={dealer_total})")

            print(f"[SERVER] Dealer stands (dealer_total={dealer_total})")

            # Decide and send round result;
            result = decide_winner(player_total, dealer_total)
            if result == RESULT_WIN:
                wins += 1
            elif result == RESULT_LOSS:
                losses += 1
            else:
                ties += 1

            conn.sendall(pack_server_payload(result, 0, 0))
            print(f"[SERVER] Result sent: {result} (W/L/T = {wins}/{losses}/{ties})")

        print(f"\n[SERVER] Finished session with {client_name}. Closing connection.")

    except (ConnectionError, socket.timeout) as e:
        print(f"[SERVER] Client {addr} disconnected/timeout: {e}")
    except Exception as e:
        print(f"[SERVER] Error handling client {addr}: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def start_tcp_server(server_name: str, host: str = "", port: int = 0):
    # Starts a TCP server socket and returns it along with the chosen port;
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen()
    tcp_port = s.getsockname()[1]
    print(f"[SERVER] TCP listening on port {tcp_port}")
    return s, tcp_port


def accept_loop(server_socket: socket.socket, server_name: str, stop_event: threading.Event):
    # Accepts incoming TCP connections and spawns a thread per client;
    server_socket.settimeout(1.0)
    while not stop_event.is_set():
        try:
            conn, addr = server_socket.accept()
        except socket.timeout:
            continue
        t = threading.Thread(
            target=handle_client,
            args=(conn, addr, server_name),
            daemon=True
        )
        t.start()

