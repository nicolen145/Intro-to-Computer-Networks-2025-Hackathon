import socket
import time

from protocol import (
    unpack_offer, pack_request,
    unpack_server_payload, pack_client_payload,
    SERVER_PAYLOAD_SIZE, RESULT_NOT_OVER, RESULT_WIN, RESULT_LOSS, RESULT_TIE
)
from cards import Card, card_value
from utils import recv_exact
from ui import format_card, banner

# Client Game Logic

# This file implements the client-side logic of the Blackjack game.
# The client listens for server offers over UDP, connects via TCP,
# interacts with the user during the game, and displays results and statistics.

UDP_PORT = 13122              # UDP port used for listening to server offers;
CLIENT_NAME = "Casino del TCP Client"  # Client team name sent to the server;


def listen_for_offer(timeout_sec: float = 15.0):
    # Listens for UDP offer messages and returns server connection details;
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Allows multiple clients on the same machine;
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except Exception:
        pass

    s.bind(("", UDP_PORT))
    s.settimeout(timeout_sec)

    print("[CLIENT] Client started, listening for offer requests...")

    while True:
        try:
            data, (ip, _) = s.recvfrom(2048)
            tcp_port, server_name = unpack_offer(data)
            print(f"[CLIENT] Received offer from {ip} (server '{server_name}', tcp_port={tcp_port})")
            return ip, tcp_port, server_name
        except socket.timeout:
            print("[CLIENT] No offers yet... still listening.")
        except Exception:
            continue


def ask_rounds():
    # Prompts the user for the number of rounds to play and validates the input;
    while True:
        raw = input("How many rounds to play? (1-255): ").strip()
        try:
            n = int(raw)
            if 1 <= n <= 255:
                return n
        except Exception:
            pass
        print("Invalid number, try again.")


def ask_decision():
    # Prompts the user to choose Hit or Stand and returns the protocol string;
    while True:
        raw = input("Hit or Stand? ").strip().lower()
        if raw in ("hit", "h"):
            return "Hittt"
        if raw in ("stand", "s"):
            return "Stand"
        print("Please type Hit or Stand.")


def result_to_text(code: int) -> str:
    # Converts a result code to a human-readable string;
    if code == RESULT_WIN:
        return "WIN"
    if code == RESULT_LOSS:
        return "LOSS"
    if code == RESULT_TIE:
        return "TIE"
    return "NOT_OVER"


def play_session(ip: str, tcp_port: int, server_name: str, rounds: int):
    # Runs a full game session with the server over TCP;
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(300.0)
    sock.connect((ip, tcp_port))
    print(f"[CLIENT] Connected to server {server_name} at {ip}:{tcp_port}")

    # Send game request to the server;
    sock.sendall(pack_request(rounds, CLIENT_NAME))

    wins = losses = ties = 0

    for r in range(1, rounds + 1):
        print(f"\n[CLIENT] --- Round {r}/{rounds} ---")

        player_cards = []
        dealer_visible = []
        dealer_hidden_and_hits = []

        # Receive initial cards: two for player and one dealer upcard;
        for i in range(3):
            payload = recv_exact(sock, SERVER_PAYLOAD_SIZE)
            result, rank, suit = unpack_server_payload(payload)
            c = Card(rank=rank, suit=suit)
            if i < 2:
                player_cards.append(c)
            else:
                dealer_visible.append(c)

        player_total = sum(card_value(c) for c in player_cards)
        print(f"[CLIENT] Your cards: {format_card(player_cards[0].rank, player_cards[0].suit)}, "
              f"{format_card(player_cards[1].rank, player_cards[1].suit)} (total={player_total})")
        print(f"[CLIENT] Dealer upcard: {format_card(dealer_visible[0].rank, dealer_visible[0].suit)} (second card hidden)")

        # Handle player turn;
        while True:
            if player_total > 21:
                print("[CLIENT] You busted!")
                break

            decision = ask_decision()
            sock.sendall(pack_client_payload(decision))

            if decision == "Stand":
                break

            payload = recv_exact(sock, SERVER_PAYLOAD_SIZE)
            result, rank, suit = unpack_server_payload(payload)
            c = Card(rank=rank, suit=suit)
            player_cards.append(c)
            player_total += card_value(c)
            print(f"[CLIENT] You got: {format_card(c.rank, c.suit)} (total={player_total})")

        # Read server messages until the final round result is received;
        while True:
            payload = recv_exact(sock, SERVER_PAYLOAD_SIZE)
            result, rank, suit = unpack_server_payload(payload)

            if result != RESULT_NOT_OVER:
                text = result_to_text(result)
                print(f"[CLIENT] Round result: {text}")
                if result == RESULT_WIN:
                    print(banner("YOU WIN! 🎉"))
                elif result == RESULT_LOSS:
                    print(banner("YOU LOSE 💀"))
                else:
                    print(banner("IT'S A TIE 🤝"))

                if result == RESULT_WIN:
                    wins += 1
                elif result == RESULT_LOSS:
                    losses += 1
                else:
                    ties += 1
                break

            c = Card(rank=rank, suit=suit)
            dealer_hidden_and_hits.append(c)
            if len(dealer_hidden_and_hits) == 1:
                print(f"[CLIENT] Dealer reveals: {format_card(c.rank, c.suit)}")
            else:
                print(f"[CLIENT] Dealer draws: {format_card(c.rank, c.suit)}")

        # Print round summary and updated statistics;
        if dealer_hidden_and_hits:
            dealer_cards_all = dealer_visible + dealer_hidden_and_hits
            dealer_total = sum(card_value(c) for c in dealer_cards_all)
            print(f"[CLIENT] Dealer cards: {', '.join(format_card(x.rank, x.suit) for x in dealer_cards_all)} (total={dealer_total})")
        print(f"[CLIENT] Current stats: W/L/T = {wins}/{losses}/{ties}")

    played = wins + losses + ties
    win_rate = (wins / played) if played else 0.0
    print(f"\n[CLIENT] Finished playing {rounds} rounds, win rate: {win_rate:.2%}")

    sock.close()


def main():
    # Main client loop that continuously searches for servers and plays sessions;
    while True:
        ip, tcp_port, server_name = listen_for_offer(timeout_sec=10.0)
        print(banner("Welcome to Casino del TCP! 🃏"))
        rounds = ask_rounds()
        try:
            play_session(ip, tcp_port, server_name, rounds)
        except (socket.timeout, ConnectionError) as e:
            print(f"[CLIENT] Connection issue: {e}")
        except Exception as e:
            print(f"[CLIENT] Error: {e}")

        print("\n[CLIENT] Returning to listen for new offers...\n")
        time.sleep(0.5)  

if __name__ == "__main__":
    main()
