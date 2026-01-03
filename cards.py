from dataclasses import dataclass
import random

# Card & Deck Utilities

# This file defines basic card and deck logic for the Blackjack game.
# It includes:
# - Card representation (rank + suit);
# - Conversion of cards to readable strings;
# - Card value calculation based on simplified Blackjack rules;
# - A Deck class that manages shuffling and drawing cards.


SUITS = ["H", "D", "C", "S"]  # Card suits; Heart, Diamond, Club, Spade;
RANKS = list(range(1, 14))    # Card ranks; 1..13 (A=1, J=11, Q=12, K=13);

RANK_TO_STR = {
    1: "A", 11: "J", 12: "Q", 13: "K"
}  # Mapping of special ranks to display characters;


@dataclass(frozen=True)
class Card:
    rank: int  # Card rank; 1..13;
    suit: int  # Card suit index; 0..3;

    def __str__(self) -> str:
        # Returns a short human-readable card representation;
        r = RANK_TO_STR.get(self.rank, str(self.rank))
        s = SUITS[self.suit] if 0 <= self.suit < 4 else "?"
        return f"{r}{s}"


def card_value(card: Card) -> int:
    # Returns the Blackjack value of a card using simplified rules;
    if card.rank == 1:
        return 11
    if 11 <= card.rank <= 13:
        return 10
    return card.rank


class Deck:
    def __init__(self):
        # Creates a standard 52-card deck and shuffles it;
        self.cards = [Card(rank=r, suit=s) for s in range(4) for r in range(1, 14)]
        self.shuffle()

    def shuffle(self):
        # Randomly shuffles the deck;
        random.shuffle(self.cards)

    def draw(self) -> Card:
        # Draws and removes the top card; resets deck if empty;
        if not self.cards:
            self.__init__()
        return self.cards.pop()
