# Special card values (Ace=14/1, Diamond-10=16/10, Spade-2=15/2) defined in Finnish Kasino rules
# See 104083758_casino_project_plan.pdf Section 6.

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

_RANK_TO_FACE = {"J": 11, "Q": 12, "K": 13}


class Card:
    """Immutable value object representing a single playing card.

    Dual-value design for Deck Casino:
      - hand_value(): value used when this card is played from the hand (target T).
      - table_value(): value used when this card sits on the table (subset sum checks).

    Special cards:
      Ace         hand=14  table=1
      Diamond-10  hand=16  table=10
      Spade-2     hand=15  table=2
    All other cards share the same hand and table value (face value).
    """

    def __init__(self, suit: str, rank: str) -> None:
        if suit not in SUITS:
            raise ValueError(f"Invalid suit: '{suit}'. Must be one of {SUITS}")
        if rank not in RANKS:
            raise ValueError(f"Invalid rank: '{rank}'. Must be one of {RANKS}")
        self._suit = suit
        self._rank = rank

    # Properties

    @property
    def suit(self) -> str:
        """The card's suit (Hearts, Diamonds, Clubs, or Spades)."""
        return self._suit

    @property
    def rank(self) -> str:
        """The card's rank (2–10, J, Q, K, or A)."""
        return self._rank

    # Value methods

    def hand_value(self) -> int:
        """Value used when this card is played from the hand."""
        if self._rank == "A":
            return 14
        if self._rank == "10" and self._suit == "Diamonds":
            return 16
        if self._rank == "2" and self._suit == "Spades":
            return 15
        if self._rank in _RANK_TO_FACE:
            return _RANK_TO_FACE[self._rank]
        return int(self._rank)

    def table_value(self) -> int:
        """Value used when this card is on the table."""
        if self._rank == "A":
            return 1
        # Diamond-10 and Spade-2 use their normal face value on the table
        if self._rank in _RANK_TO_FACE:
            return _RANK_TO_FACE[self._rank]
        return int(self._rank)

    def is_special(self) -> bool:
        """Returns True for cards with a boosted hand value (Ace, Diamond-10, Spade-2)."""
        if self._rank == "A":
            return True
        if self._rank == "10" and self._suit == "Diamonds":
            return True
        if self._rank == "2" and self._suit == "Spades":
            return True
        return False

    # Dunder helpers

    def __str__(self) -> str:
        return f"{self._rank} of {self._suit}"

    def __repr__(self) -> str:
        return f"Card('{self._suit}', '{self._rank}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self._suit == other._suit and self._rank == other._rank

    def __hash__(self) -> int:
        return hash((self._suit, self._rank))
