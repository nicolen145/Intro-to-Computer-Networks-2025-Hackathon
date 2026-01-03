import struct

# Protocol Definitions & Usage Instructions

# This file defines the binary protocol used for communication between
# the Blackjack server and client.
#
# Message flow:
#   Server -> Client (UDP): Offer message (server discovery)
#   Client -> Server (TCP): Request message (number of rounds)
#   Client <-> Server (TCP): Payload messages during the game


MAGIC_COOKIE = 0xabcddcba

MSG_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4

# Server round result codes
RESULT_NOT_OVER = 0x0
RESULT_TIE = 0x1
RESULT_LOSS = 0x2
RESULT_WIN = 0x3

# Binary formats (network byte order = big endian)
OFFER_FMT = "!IBH32s"       # cookie(4) | type(1) | tcp_port(2) | server_name(32)
REQUEST_FMT = "!IBB32s"     # cookie(4) | type(1) | rounds(1) | client_name(32)

# Payload formats differ by direction
CLIENT_PAYLOAD_FMT = "!IB5s"       # cookie(4) | type(1) | decision(5 bytes)
SERVER_PAYLOAD_FMT = "!IBBHB"      # cookie(4) | type(1) | result(1) | rank(2) | suit(1)

# Pre-calculated sizes for safe TCP reading
OFFER_SIZE = struct.calcsize(OFFER_FMT)
REQUEST_SIZE = struct.calcsize(REQUEST_FMT)
CLIENT_PAYLOAD_SIZE = struct.calcsize(CLIENT_PAYLOAD_FMT)
SERVER_PAYLOAD_SIZE = struct.calcsize(SERVER_PAYLOAD_FMT)


def pack_name_32(name: str) -> bytes:
    # Encodes a name to exactly 32 bytes using padding or truncation;
    raw = name.encode("utf-8", errors="ignore")
    raw = raw[:32]
    return raw.ljust(32, b"\x00")


def unpack_name_32(data: bytes) -> str:
    # Decodes a 32-byte padded name back into a string;
    return data.split(b"\x00", 1)[0].decode("utf-8", errors="ignore")


def pack_offer(tcp_port: int, server_name: str) -> bytes:
    # Packs a UDP offer message sent from server to clients;
    return struct.pack(
        OFFER_FMT,
        MAGIC_COOKIE,
        MSG_TYPE_OFFER,
        tcp_port,
        pack_name_32(server_name),
    )


def unpack_offer(data: bytes):
    # Unpacks and validates an incoming offer message;
    if len(data) < OFFER_SIZE:
        raise ValueError("offer too short")

    cookie, mtype, tcp_port, name_b = struct.unpack(OFFER_FMT, data[:OFFER_SIZE])
    if cookie != MAGIC_COOKIE or mtype != MSG_TYPE_OFFER:
        raise ValueError("invalid offer")

    return tcp_port, unpack_name_32(name_b)


def pack_request(rounds: int, client_name: str) -> bytes:
    # Packs a TCP request message containing the number of rounds and client name;
    rounds = max(1, min(255, int(rounds)))
    return struct.pack(
        REQUEST_FMT,
        MAGIC_COOKIE,
        MSG_TYPE_REQUEST,
        rounds,
        pack_name_32(client_name),
    )


def unpack_request(data: bytes):
    # Unpacks and validates an incoming request message;
    if len(data) < REQUEST_SIZE:
        raise ValueError("request too short")

    cookie, mtype, rounds, name_b = struct.unpack(REQUEST_FMT, data[:REQUEST_SIZE])
    if cookie != MAGIC_COOKIE or mtype != MSG_TYPE_REQUEST:
        raise ValueError("invalid request")

    return rounds, unpack_name_32(name_b)


def pack_client_payload(decision_text_5: str) -> bytes:
    # Packs a client decision payload containing "Hittt" or "Stand";
    if decision_text_5 not in ("Hittt", "Stand"):
        raise ValueError("decision must be 'Hittt' or 'Stand'")

    return struct.pack(
        CLIENT_PAYLOAD_FMT,
        MAGIC_COOKIE,
        MSG_TYPE_PAYLOAD,
        decision_text_5.encode("ascii"),
    )


def unpack_client_payload(data: bytes) -> str:
    # Unpacks and returns the player decision from a client payload;
    if len(data) < CLIENT_PAYLOAD_SIZE:
        raise ValueError("client payload too short")

    cookie, mtype, decision_b = struct.unpack(
        CLIENT_PAYLOAD_FMT,
        data[:CLIENT_PAYLOAD_SIZE],
    )
    if cookie != MAGIC_COOKIE or mtype != MSG_TYPE_PAYLOAD:
        raise ValueError("invalid client payload")

    return decision_b.decode("ascii", errors="ignore")


def pack_server_payload(result: int, rank: int, suit: int) -> bytes:
    # Packs a server payload containing the round result and card information;
    result = int(result) & 0xFF
    rank = int(rank) & 0xFFFF
    suit = int(suit) & 0xFF

    return struct.pack(
        SERVER_PAYLOAD_FMT,
        MAGIC_COOKIE,
        MSG_TYPE_PAYLOAD,
        result,
        rank,
        suit,
    )


def unpack_server_payload(data: bytes):
    # Unpacks and returns the round result and card data from a server payload;
    if len(data) < SERVER_PAYLOAD_SIZE:
        raise ValueError("server payload too short")

    cookie, mtype, result, rank, suit = struct.unpack(
        SERVER_PAYLOAD_FMT,
        data[:SERVER_PAYLOAD_SIZE],
    )
    if cookie != MAGIC_COOKIE or mtype != MSG_TYPE_PAYLOAD:
        raise ValueError("invalid server payload")

    return result, rank, suit
