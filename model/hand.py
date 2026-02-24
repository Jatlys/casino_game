from model.card import Card


class Hand:
    """Aggregates Card objects for one participant.

    get_value() sums each card's hand_value(). Game-specific logic is
    handled at the game layer, not here.
    """

    def __init__(self, owner: str = "") -> None:
        self._cards: list[Card] = []
        self._owner = owner

    # Properties

    @property
    def cards(self) -> list[Card]:
        return list(self._cards)

    @property
    def owner(self) -> str:
        return self._owner

    # Mutation methods

    def add_card(self, card: Card) -> None:
        """Append a card to the hand."""
        self._cards.append(card)

    def remove_card(self, card: Card) -> None:
        """Remove a specific card from the hand.

        Raises:
            ValueError: if the card is not present.
        """
        if card not in self._cards:
            raise ValueError(f"{card} is not in {self._owner}'s hand")
        self._cards.remove(card)

    # Query methods

    def card_count(self) -> int:
        """Return the number of cards currently in the hand."""
        return len(self._cards)

    def get_value(self) -> int:
        """Return the sum of hand_value() for every card in the hand."""
        return sum(card.hand_value() for card in self._cards)

    def is_empty(self) -> bool:
        """Return True when the hand contains no cards."""
        return len(self._cards) == 0

    # Dunder helpers

    def __str__(self) -> str:
        if self._cards:
            return ", ".join(str(c) for c in self._cards)
        return "(empty hand)"

    def __repr__(self) -> str:
        return f"Hand(owner='{self._owner}', cards={self._cards!r})"
