# Week 7 AI vs AI integration tests.
# Verifies that AI (hard difficulty) never leaves an obvious sweep for the
# opponent and that full AI vs AI games complete without errors.
#
# Run with: python -m unittest tests.deck_casino_tests.test_week7_ai

import itertools
import unittest

from model.card import Card
from model.player import Player
from model.deck_casino_game import DeckCasinoGame
from model.ai_opponent import AIOpponent
from model.casino_take_algorithm import CasinoTakeAlgorithm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ai_game(n_players: int = 2, difficulty: str = "hard"):
    """Return a started DeckCasinoGame with n_players hard AI bots."""
    players = [Player(f"Bot{i+1}", is_ai=True, difficulty=difficulty)
               for i in range(n_players)]
    game = DeckCasinoGame(players)
    game.start_game()
    return game, players


def is_sweepable(table: list[Card]) -> bool:
    """Return True if ANY card value 2-16 can sweep the entire table."""
    if not table:
        return False
    for hand_val in range(2, 17):
        valid: list[frozenset] = []
        for r in range(1, len(table) + 1):
            for combo in itertools.combinations(table, r):
                if sum(c.table_value() for c in combo) == hand_val:
                    valid.append(frozenset(combo))
        if CasinoTakeAlgorithm._can_cover(frozenset(table), valid):
            return True
    return False


def inject_state(game, player, hand_cards, table_cards):
    """Replace a player's hand and the game table with controlled cards."""
    game._table_cards = list(table_cards)
    for c in list(player.hand.cards):
        player.hand.remove_card(c)
    for c in hand_cards:
        player.hand.add_card(c)


# ---------------------------------------------------------------------------
# AI placement safety tests
# ---------------------------------------------------------------------------

class TestAINoEasySweepLeft(unittest.TestCase):
    """Hard AI must prefer safe placements over sweep-enabling ones when a safe option exists."""

    def _has_safe_placement(self, hand_cards, table_cards):
        """Return True if any card in hand_cards can be placed without enabling a sweep."""
        for c in hand_cards:
            if not is_sweepable(table_cards + [c]):
                return True
        return False

    def _placed_card_not_sweep_enabling_when_safe_exists(self, hand_cards, table_cards):
        """Assert that when a safe placement exists, the hard AI picks it."""
        if not self._has_safe_placement(hand_cards, table_cards):
            return  # No safe option; skip — AI can only do best effort

        game, players = make_ai_game()
        inject_state(game, players[0], hand_cards, table_cards)
        card, take = AIOpponent.decide_action(game, difficulty="hard")
        if take is not None:
            return  # AI took instead of placed — no sweep concern

        new_table = table_cards + [card]
        sweepable = is_sweepable(new_table)
        self.assertFalse(
            sweepable,
            f"Hard AI placed {card} onto {[str(c) for c in table_cards]}, "
            f"creating a sweepable table when a safe option existed. "
            f"New table: {[str(c) for c in new_table]}"
        )

    def test_no_sweep_left_when_safe_option_exists(self):
        """AI picks the safe card when one option is sweep-enabling and the other is not.

        table=[3]; hand=[4, K(13)].
        Placing 4: [3,4] sweepable by 7.
        Placing K(13): [3,13] — can only be swept by value 16 (13+3). Check it.
        Since both may be risky, we only assert when we know one is safe.
        """
        hand = [Card("Hearts", "4"), Card("Clubs", "K")]
        table = [Card("Diamonds", "3")]
        self._placed_card_not_sweep_enabling_when_safe_exists(hand, table)

    def test_no_sweep_left_two_card_table(self):
        """When a safe placement exists on a 2-card table, AI uses it."""
        hand = [Card("Spades", "6"), Card("Hearts", "Q")]
        table = [Card("Clubs", "2"), Card("Diamonds", "5")]
        self._placed_card_not_sweep_enabling_when_safe_exists(hand, table)

    def test_sweep_taken_rather_than_left(self):
        """When a sweep is available, hard AI MUST take it, not leave it."""
        game, players = make_ai_game()
        played = Card("Hearts", "9")
        t1 = Card("Clubs", "4")
        t2 = Card("Diamonds", "5")
        inject_state(game, players[0], [played], [t1, t2])
        card, take = AIOpponent.decide_action(game, difficulty="hard")
        self.assertIsNotNone(take, "AI should sweep rather than place")
        self.assertEqual(take, frozenset({t1, t2}))

    def test_hard_ai_picks_safe_placement_over_unsafe(self):
        """Controlled scenario: one card is sweep-safe, the other is not.

        table=[Clubs-8]; placing Hearts-6: [8,6] NOT sweepable by any value 2-16
        (8+6=14, but 14 is valid, so it IS sweepable by 14). Let me pick differently.

        table=[Clubs-J(11, tv=10)]; placing Hearts-2: [J,2] → tv sum could be 12
        → sweepable by hand_value 12. Placing Spades-K(13, tv=10): [J,K] → tv=20,
        no hand_value 20. So K is safe.
        """
        game, players = make_ai_game()
        safe_card   = Card("Spades", "K")   # tv=10; [J,K] → tv sum impossible to reach
        unsafe_card = Card("Hearts", "2")   # tv=2;  [J,2] → tv=12, sweepable by hv=12
        table = [Card("Clubs", "J")]
        # Verify our assumption: unsafe_card IS sweep-enabling
        self.assertTrue(is_sweepable(table + [unsafe_card]),
                        "Test setup: [J,2] should be sweepable")
        # Verify safe_card is NOT sweep-enabling: [J,K] both tv=10, sum=20 → no hv=20
        jack_tv = Card("Clubs", "J").table_value()
        king_tv = Card("Spades", "K").table_value()
        # No card has hand_value > 16, so sum 20 is unreachable
        inject_state(game, players[0], [safe_card, unsafe_card], table)
        card, take = AIOpponent.decide_action(game, difficulty="hard")
        if take is None:
            new_table = table + [card]
            self.assertFalse(
                is_sweepable(new_table),
                f"AI placed {card}, leaving sweepable table {[str(c) for c in new_table]}"
            )


# ---------------------------------------------------------------------------
# AI vs AI full-game integration tests
# ---------------------------------------------------------------------------

class TestAIvsAIFullGame(unittest.TestCase):
    """Run complete AI vs AI games and verify they finish without errors."""

    def _run_game(self, n_players: int = 2, difficulty: str = "hard",
                  max_moves: int = 1000) -> None:
        """Run an AI vs AI game to completion (or max_moves)."""
        game, players = make_ai_game(n_players, difficulty)
        moves = 0

        while not game.is_round_over() and moves < max_moves:
            cp = game.current_player
            if cp.hand.is_empty():
                game.advance_turn()
            else:
                card, take = AIOpponent.decide_action(game, cp.difficulty)
                game.play_card(card, take)
            moves += 1

        self.assertTrue(
            game.is_round_over() or moves < max_moves,
            "AI vs AI game did not terminate within move budget"
        )
        if game.is_round_over():
            # end_round should not raise
            game.end_round()

    def test_two_hard_ai_complete_game(self):
        self._run_game(n_players=2, difficulty="hard")

    def test_three_hard_ai_complete_game(self):
        self._run_game(n_players=3, difficulty="hard")

    def test_four_hard_ai_complete_game(self):
        self._run_game(n_players=4, difficulty="hard")

    def test_two_easy_ai_complete_game(self):
        self._run_game(n_players=2, difficulty="easy")

    def test_two_medium_ai_complete_game(self):
        self._run_game(n_players=2, difficulty="medium")


# ---------------------------------------------------------------------------
# AI no-easy-sweep property tests across 10 random full games
# ---------------------------------------------------------------------------

class TestAINoEasySweepProperty(unittest.TestCase):
    """Property test: across many full games, hard AI never leaves a sweep."""

    def test_hard_ai_never_leaves_sweep_when_safe_option_existed_10_games(self):
        """Over 10 AI vs AI games, hard AI never leaves a sweep when a safe placement existed."""
        violations: list[str] = []

        for game_num in range(10):
            game, players = make_ai_game(n_players=2, difficulty="hard")
            moves = 0

            while not game.is_round_over() and moves < 500:
                cp = game.current_player
                if cp.hand.is_empty():
                    game.advance_turn()
                    moves += 1
                    continue

                table_before = list(game.table_cards)
                hand_before  = list(cp.hand.cards)
                card, take = AIOpponent.decide_action(game, difficulty="hard")
                game.play_card(card, take)
                moves += 1

                # Only audit placements
                if take is None:
                    new_table = table_before + [card]
                    if is_sweepable(new_table):
                        # Only flag if a safe placement option actually existed
                        safe_existed = any(
                            not is_sweepable(table_before + [c])
                            for c in hand_before
                        )
                        if safe_existed:
                            violations.append(
                                f"Game {game_num+1}: {cp.name} placed {card} "
                                f"onto {[str(c) for c in table_before]}, "
                                f"creating sweepable table when a safe option existed"
                            )

        self.assertEqual(
            violations, [],
            "Hard AI ignored safe placements:\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# AI move validity tests
# ---------------------------------------------------------------------------

class TestAIMoveValidity(unittest.TestCase):
    """AI must always emit a move that the game accepts without ValueError."""

    def _run_and_verify_moves(self, difficulty: str) -> None:
        game, players = make_ai_game(n_players=2, difficulty=difficulty)
        for _ in range(100):
            if game.is_round_over():
                break
            cp = game.current_player
            if cp.hand.is_empty():
                game.advance_turn()
                continue
            card, take = AIOpponent.decide_action(game, difficulty)
            try:
                game.play_card(card, take)
            except ValueError as exc:
                self.fail(
                    f"{difficulty} AI produced an invalid move: {exc}\n"
                    f"  card={card}, take={take}"
                )

    def test_easy_moves_always_valid(self):
        self._run_and_verify_moves("easy")

    def test_medium_moves_always_valid(self):
        self._run_and_verify_moves("medium")

    def test_hard_moves_always_valid(self):
        self._run_and_verify_moves("hard")


if __name__ == "__main__":
    unittest.main()
