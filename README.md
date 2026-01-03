# Intro to Nets 2025 Hackaton
# Blackjack Client-Server 🃏

## Team Name
Casino del TCP

## Team Members
- Lilach Zaks
- Gal Omesi
- Nicole Neginsky

## Overview
This project implements a simplified Blackjack game as a client–server application using network programming in Python.

- The server acts as the dealer:
  - Broadcasts game offers using UDP
  - Accepts TCP connections from clients
  - Manages all Blackjack logic and game rules

- The client acts as the player:
  - Listens for server offers via UDP
  - Connects to a server using TCP
  - Plays multiple Blackjack rounds interactively
  - Displays results, statistics, and colorful UI elements

The implementation strictly follows the protocol and rules defined in the assignment.

---

## Features
- UDP broadcast discovery (no hard-coded IPs)
- TCP-based reliable gameplay
- Support for multiple clients simultaneously
- Simplified Blackjack rules (as defined in assignment)
- Clear separation between:
  - Networking
  - Protocol encoding/decoding
  - Game logic
  - UI
- Fun client UI:
  - Colored card suits (♥ ♦ ♣ ♠)
  - Big banners: YOU WIN / YOU LOSE / IT'S A TIE
  - Per-round and session statistics
- Proper error handling and timeouts
- No busy-waiting

---

## File Structure
```text
blackjack/
├── server.py        # Server entry point
├── server_tcp.py    # TCP server + game handling
├── server_udp.py    # UDP offer broadcaster
├── client.py        # Client application
├── protocol.py     # Packet formats (pack/unpack)
├── cards.py        # Card & deck logic
├── utils.py        # TCP helpers (recv_exact)
├── ui.py           # Client-side UI (colors, banners)
├── README.md
