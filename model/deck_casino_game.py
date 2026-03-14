from model.card import Card
from model.deck import Deck
from model.player import Player
from model.casino_take_algorithm import CasinoTakeAlgorithm


class DeckCasinoGame:
    """Core game loop for Deck Casino.

    Rules (casino_card_game.md):
    - Each player gets 4 cards; 4 cards dealt to table; rest = stock pile.
    - On each turn a player plays 1 card: take matching table cards OR place on table.
    - After playing, draw 1 card from stock (if available).
    - Sweep: taking all table cards at once scores 1 sweep point.
    - Round ends when stock and all hands are empty.
    - Last player to take cards collects remaining table cards.
    - Game ends when any player reaches 16 points.
    """

    WIN_SCORE = 16

    def __init__(self, players: list[Player]) -> None:
        if len(players) < 2:
            raise ValueError("Deck Casino requires at least 2 players.")
        self._players = players
        self._deck = Deck()
        self._table_cards: list[Card] = []
        self._turn_index: int = 0
        self._last_taker: Player | None = None

    # Setup

    def start_game(self) -> None:
        """Shuffle deck, deal 4 cards to table and 4 cards to each player."""
        self._deck = Deck()
        self._deck.shuffle()
        self._table_cards = self._deck.deal(4)
        for player in self._players:
            player.reset_for_round()
            for card in self._deck.deal(4):
                player.hand.add_card(card)
        self._last_taker = None
        self._turn_index = 0

    # Turn actions

    def play_card(self, card: Card, take: frozenset | None = None) -> None:
        """Execute the current player's turn.

        Args:
            card: Card from the current player's hand to play.
            take: Frozenset of table cards to take, or None to place the card.

        Raises:
            ValueError: If card is not in the player's hand, or if take is invalid.
        """
        player = self.current_player

        if card not in player.hand.cards:
            raise ValueError(f"{card} is not in {player.name}'s hand.")

        player.hand.remove_card(card)

        if take is not None:
            if not CasinoTakeAlgorithm.is_valid_take(card, take, self._table_cards):
                raise ValueError(f"Invalid take: {take} with played card {card}.")
            for taken_card in take:
                self._table_cards.remove(taken_card)
            player.add_to_collection([card] + list(take))
            self._last_taker = player
            self.check_sweep()
        else:
            self._table_cards.append(card)

        # Replenish hand from stock
        if not self._deck.is_empty():
            player.hand.add_card(self._deck.deal(1)[0])

        self.advance_turn()

    def check_sweep(self) -> None:
        """Award a sweep to the current player if the table is now empty."""
        if len(self._table_cards) == 0:
            self.current_player.add_sweep()

    def advance_turn(self) -> None:
        """Move to the next player."""
        self._turn_index = (self._turn_index + 1) % len(self._players)

    # Round end

    def is_round_over(self) -> bool:
        """True when the stock is empty and all players' hands are empty."""
        return self._deck.is_empty() and all(
            p.hand.is_empty() for p in self._players
        )

    def end_round(self) -> None:
        """Finalize the round: award remaining table cards, then calculate scores."""
        if self._last_taker is not None and self._table_cards:
            self._last_taker.add_to_collection(list(self._table_cards))
            self._table_cards.clear()
        self.calculate_scores()

    def calculate_scores(self) -> None:
        """Award round points to all players based on their collections."""
        # Sweeps
        for player in self._players:
            if player.sweeps > 0:
                player.add_score(player.sweeps)

        # Each Ace collected
        for player in self._players:
            aces = sum(1 for c in player.collection if c.rank == "A")
            if aces:
                player.add_score(aces)

        # Most cards (tie = no point)
        max_cards = max(len(p.collection) for p in self._players)
        card_leaders = [p for p in self._players if len(p.collection) == max_cards]
        if len(card_leaders) == 1:
            card_leaders[0].add_score(1)

        # Most spades (tie = no point) — 2 points
        spade_counts = {p: sum(1 for c in p.collection if c.suit == "Spades") for p in self._players}
        max_spades = max(spade_counts.values())
        spade_leaders = [p for p in self._players if spade_counts[p] == max_spades]
        if len(spade_leaders) == 1:
            spade_leaders[0].add_score(2)

        # Diamond-10 holder — 2 points
        for player in self._players:
            if any(c.suit == "Diamonds" and c.rank == "10" for c in player.collection):
                player.add_score(2)
                break

        # Spade-2 holder — 1 point
        for player in self._players:
            if any(c.suit == "Spades" and c.rank == "2" for c in player.collection):
                player.add_score(1)
                break

    def has_winner(self) -> bool:
        """True if any player has reached WIN_SCORE (16) points."""
        return any(p.total_score >= self.WIN_SCORE for p in self._players)

    # Properties

    @property
    def current_player(self) -> Player:
        return self._players[self._turn_index]

    @property
    def table_cards(self) -> list[Card]:
        return list(self._table_cards)

    @property
    def players(self) -> list[Player]:
        return list(self._players)

    @property
    def deck(self) -> Deck:
        return self._deck

    # Dunder helpers

    def __repr__(self) -> str:
        return (
            f"DeckCasinoGame(players={[p.name for p in self._players]}, "
            f"table={len(self._table_cards)} cards, "
            f"stock={len(self._deck)} cards, "
            f"turn={self.current_player.name})"
        )
