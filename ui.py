import os

# Console Formatting Utilities

# This file provides helper functions for formatting console output.
# It handles optional ANSI color support, card symbols and colors,
# and simple banner printing to make the game output more readable.


USE_COLOR = True  # Global flag to enable or disable colored output;


def supports_color() -> bool:
    # Checks whether the current terminal supports ANSI colors;
    # Enables color support on Windows if possible;
    if os.name != "nt":
        return True
    try:
        import colorama  # optional
        colorama.just_fix_windows_console()
        return True
    except Exception:
        return False


_COLOR_OK = supports_color()  # Cached result for color support;


def c(text: str, code: str) -> str:
    # Wraps text with ANSI color codes if coloring is enabled;
    if not USE_COLOR or not _COLOR_OK:
        return text
    return f"\033[{code}m{text}\033[0m"




def rank_str(rank: int) -> str:
    # Converts a card rank number into a printable string;
    return {1: "A", 11: "J", 12: "Q", 13: "K"}.get(rank, str(rank))


def format_card(rank: int, suit: int) -> str:
    # Formats a card with rank and colored suit symbol;
    r = rank_str(rank)
    sym = suit_symbol(suit)

    # Hearts and Diamonds are red; Clubs and Spades are cyan;
    if suit in (0, 1):
        sym = c(sym, "31")
    else:
        sym = c(sym, "36")

    return f"{r}{sym}"


def banner(text: str) -> str:
    # Creates a simple colored banner around a given text;
    line = "═" * (len(text) + 10)
    return "\n".join([
        c(line, "35"),
        c(f"   {text}   ", "1;33"),
        c(line, "35"),
    ])
