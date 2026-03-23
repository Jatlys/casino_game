import itertools
import random

from model.card import Card
from model.casino_take_algorithm import CasinoTakeAlgorithm


class AIOpponent:
    """Strategic AI for Deck Casino with three difficulty levels.

    Easy   — random legal move; no strategy.
    Medium — sweep detection, maximise cards, lowest placement (priorities 1, 3, 6).
    Hard   — full 6-priority strategy (default).
    """

    # Cards worth protecting / capturing
    _PRIZE_CARDS = frozenset({Card("Diamonds", "10"), Card("Spades", "2")})

    @staticmethod
    def decide_action(game, difficulty: str = "hard") -> tuple[Card, frozenset | None]:
        """Choose the best action for the current AI player.

        Args:
            game: A running DeckCasinoGame instance.
            difficulty: "easy", "medium", or "hard".

        Returns:
            (card_to_play, take) where take is a frozenset of table cards to
            collect, or None to place the card on the table.
        """
        if difficulty == "easy":
            return AIOpponent._decide_easy(game)
        if difficulty == "medium":
            return AIOpponent._decide_medium(game)
        return AIOpponent._decide_hard(game)

    # ------------------------------------------------------------------
    # Easy — random legal move
    # ------------------------------------------------------------------

    @staticmethod
    def _decide_easy(game) -> tuple[Card, frozenset | None]:
        """Pick any random valid take, or place a random card."""
        player = game.current_player
        table: list[Card] = game.table_cards
        hand_cards: list[Card] = list(player.hand.cards)

        options: list[tuple[Card, frozenset]] = []
        for card in hand_cards:
            for take in CasinoTakeAlgorithm.get_valid_takes(card, table):
                options.append((card, take))

        if options:
            return random.choice(options)
        return random.choice(hand_cards), None

    # ------------------------------------------------------------------
    # Medium — priorities 1, 3, 6 only
    # ------------------------------------------------------------------

    @staticmethod
    def _decide_medium(game) -> tuple[Card, frozenset | None]:
        """Apply sweep detection, maximise cards, and place lowest-value card."""
        player = game.current_player
        table: list[Card] = game.table_cards
        hand_cards: list[Card] = list(player.hand.cards)

        all_options: list[tuple[Card, frozenset]] = []
        for card in hand_cards:
            for take in CasinoTakeAlgorithm.get_valid_takes(card, table):
                all_options.append((card, take))
            if table:
                full_take = frozenset(table)
                if CasinoTakeAlgorithm.is_valid_take(card, full_take, table):
                    if (card, full_take) not in all_options:
                        all_options.append((card, full_take))

        if not all_options:
            # Priority 6: place lowest hand-value card
            return min(hand_cards, key=lambda c: c.hand_value()), None

        # Priority 1: Sweep
        full_table = frozenset(table)
        sweep_options = [(c, t) for c, t in all_options if t == full_table]
        if sweep_options:
            return min(sweep_options, key=lambda x: x[0].hand_value())

        # Priority 3: Maximise cards taken
        max_count = max(len(t) for _, t in all_options)
        max_options = [(c, t) for c, t in all_options if len(t) == max_count]
        return max_options[0]

    # ------------------------------------------------------------------
    # Hard — full 6-priority strategy
    # ------------------------------------------------------------------

    @staticmethod
    def _decide_hard(game) -> tuple[Card, frozenset | None]:
        """Full 6-priority strategy: sweep → prize cards → max count → special preference
        → sweep-safe placement → lowest hand value."""
        player = game.current_player
        table: list[Card] = game.table_cards  # defensive copy
        hand_cards: list[Card] = list(player.hand.cards)

        # --- Collect all valid (card, take) options ---
        all_options: list[tuple[Card, frozenset]] = []
        for card in hand_cards:
            for take in CasinoTakeAlgorithm.get_valid_takes(card, table):
                all_options.append((card, take))
            # Also check combined sweep take (all table cards at once)
            if table:
                full_take = frozenset(table)
                if CasinoTakeAlgorithm.is_valid_take(card, full_take, table):
                    if (card, full_take) not in all_options:
                        all_options.append((card, full_take))

        if not all_options:
            # No takes available — must place a card
            return AIOpponent._choose_placement(hand_cards, table), None

        # Priority 1: Sweep opportunity (take all table cards)
        full_table = frozenset(table)
        sweep_options = [(c, t) for c, t in all_options if t == full_table]
        if sweep_options:
            # Use the least valuable hand card so high-value cards are preserved
            return min(sweep_options, key=lambda x: x[0].hand_value())

        # Priority 2: Capture Diamond-10 or Spade-2 from table
        prize_options = [
            (c, t) for c, t in all_options if AIOpponent._PRIZE_CARDS & t
        ]
        if prize_options:
            return max(prize_options, key=lambda x: len(x[1]))

        # Priority 3: Maximise cards taken
        max_count = max(len(t) for _, t in all_options)
        max_options = [(c, t) for c, t in all_options if len(t) == max_count]

        # Priority 4: Among max-count options, prefer takes with special cards
        special_options = [
            (c, t) for c, t in max_options if any(card.is_special() for card in t)
        ]
        if special_options:
            return special_options[0]

        return max_options[0]

    # ------------------------------------------------------------------
    # Placement helpers (priorities 5 & 6)
    # ------------------------------------------------------------------

    @staticmethod
    def _choose_placement(hand_cards: list[Card], table: list[Card]) -> Card:
        """Pick the safest card to place on the table.

        Priority 5: avoid creating a sweep opportunity for opponents.
        Priority 6: fall back to the card with the lowest hand value.
        """
        candidates = sorted(hand_cards, key=lambda c: c.hand_value())
        safe = [c for c in candidates if not AIOpponent._placement_enables_sweep(c, table)]
        return safe[0] if safe else candidates[0]

    @staticmethod
    def _placement_enables_sweep(card: Card, table: list[Card]) -> bool:
        """Return True if placing card on the table would allow any hand value to sweep."""
        new_table = table + [card]
        for hand_val in range(2, 17):
            if AIOpponent._sweepable_by_value(hand_val, new_table):
                return True
        return False

    @staticmethod
    def _sweepable_by_value(hand_value: int, table: list[Card]) -> bool:
        """Return True if a card with hand_value could take every card on the table."""
        if not table:
            return False
        valid_subsets: list[frozenset] = []
        for r in range(1, len(table) + 1):
            for combo in itertools.combinations(table, r):
                if sum(c.table_value() for c in combo) == hand_value:
                    valid_subsets.append(frozenset(combo))
        return CasinoTakeAlgorithm._can_cover(frozenset(table), valid_subsets)
