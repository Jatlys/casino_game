import itertools


class CasinoTakeAlgorithm:
    """Algorithm for determining valid card takes in Deck Casino.

    A played card can take any non-empty subset of table cards whose
    table_value() sum equals the played card's hand_value().
    Multiple non-overlapping valid subsets may be taken simultaneously.
    """

    @staticmethod
    def get_valid_takes(played_card, table_cards: list) -> list[frozenset]:
        """Return all valid non-empty subsets of table_cards.

        Each returned frozenset contains cards whose table_value() sum
        equals played_card.hand_value(). Both single-card matches and
        multi-card sum matches are returned.

        Args:
            played_card: Card being played from hand.
            table_cards: Current cards on the table.

        Returns:
            List of frozensets, each a valid take subset.
            Empty list if no valid takes exist (including empty table).
        """
        target = played_card.hand_value()
        valid = []
        for r in range(1, len(table_cards) + 1):
            for combo in itertools.combinations(table_cards, r):
                if sum(c.table_value() for c in combo) == target:
                    valid.append(frozenset(combo))
        return valid

    @staticmethod
    def is_valid_take(played_card, chosen_cards: frozenset, table_cards: list) -> bool:
        """Check whether chosen_cards is a valid take for played_card.

        The chosen set must be decomposable into one or more non-overlapping
        valid subsets (each summing to played_card.hand_value()).

        Args:
            played_card: Card being played from hand.
            chosen_cards: Frozenset of table cards the player wants to take.
            table_cards: Current cards on the table.

        Returns:
            True if chosen_cards is a valid take, False otherwise.
        """
        if not chosen_cards:
            return False
        if not chosen_cards.issubset(set(table_cards)):
            return False

        valid_subsets = CasinoTakeAlgorithm.get_valid_takes(played_card, list(chosen_cards))

        # Check if chosen_cards can be covered by non-overlapping valid subsets
        return CasinoTakeAlgorithm._can_cover(frozenset(chosen_cards), valid_subsets)

    @staticmethod
    def explain_invalid_take(played_card, chosen_cards: frozenset, table_cards: list) -> str:
        """Return a human-readable reason why chosen_cards is not a valid take."""
        target = played_card.hand_value()

        if not chosen_cards.issubset(set(table_cards)):
            missing = chosen_cards - set(table_cards)
            missing_str = ", ".join(str(c) for c in missing)
            return f"{missing_str} {'is' if len(missing) == 1 else 'are'} not on the table."

        all_valid = CasinoTakeAlgorithm.get_valid_takes(played_card, table_cards)
        if not all_valid:
            return (
                f"{played_card} has a value of {target}, but no combination "
                f"of table cards sums to {target}."
            )

        chosen_sum = sum(c.table_value() for c in chosen_cards)
        if chosen_sum != target and len(chosen_cards) == 1:
            card = next(iter(chosen_cards))
            return (
                f"{card} has a table value of {card.table_value()}, "
                f"but {played_card} requires a sum of {target}."
            )

        return (
            f"The selected cards (sum = {chosen_sum}) cannot be split into "
            f"valid groups that each sum to {target} (the value of {played_card})."
        )

    @staticmethod
    def _can_cover(remaining: frozenset, valid_subsets: list[frozenset]) -> bool:
        """Recursively check if remaining cards can be partitioned into valid subsets."""
        if not remaining:
            return True
        for subset in valid_subsets:
            if subset.issubset(remaining):
                if CasinoTakeAlgorithm._can_cover(remaining - subset, valid_subsets):
                    return True
        return False
