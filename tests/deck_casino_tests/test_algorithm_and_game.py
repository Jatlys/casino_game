# Unit tests for CasinoTakeAlgorithm and DeckCasinoGame.
# Run with: python -m unittest tests/deck_casino_tests/test_algorithm_and_game.py
# Ref: /Project Overview/casino_card_game.md (game rules and take examples) from A+ https://plus.cs.aalto.fi/y2/2026/project_topics/topics_pelit_104kasino_en/

import unittest

from model.card import Card
from model.player import Player
from model.casino_take_algorithm import CasinoTakeAlgorithm
from model.deck_casino_game import DeckCasinoGame


def make_game(names=("Alice", "Bob")):
    """Return a started DeckCasinoGame with the given player names."""
    players = [Player(n) for n in names]
    game = DeckCasinoGame(players)
    game.start_game()
    return game, players


def inject_state(game, player, hand_cards, table_cards):
    """Replace the game's table and a player's hand with controlled cards."""
    game._table_cards = list(table_cards)
    for c in list(player.hand.cards):
        player.hand.remove_card(c)
    for c in hand_cards:
        player.hand.add_card(c)


class TestCasinoTakeAlgorithm(unittest.TestCase):
    """Tests for get_valid_takes() and is_valid_take()."""

    # get_valid_takes() — edge cases

    def test_empty_table_returns_empty(self):
        played = Card("Hearts", "7")
        self.assertEqual(CasinoTakeAlgorithm.get_valid_takes(played, []), [])

    def test_no_match_returns_empty(self):
        """No card or combination sums to played card's hand value."""
        played = Card("Hearts", "9")
        table = [Card("Clubs", "2"), Card("Diamonds", "3")]  # max sum 5 ≠ 9
        self.assertEqual(CasinoTakeAlgorithm.get_valid_takes(played, table), [])

    # get_valid_takes() — single-value matches

    def test_single_card_value_match(self):
        """Single table card whose table_value equals played hand_value."""
        played = Card("Hearts", "7")
        table = [Card("Clubs", "7"), Card("Diamonds", "3")]
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        self.assertIn(frozenset({Card("Clubs", "7")}), takes)

    def test_all_same_value_each_is_valid(self):
        """Three table cards each matching played value → three single-card subsets."""
        played = Card("Hearts", "7")
        table = [Card("Clubs", "7"), Card("Diamonds", "7"), Card("Spades", "7")]
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        singles = [t for t in takes if len(t) == 1]
        self.assertEqual(len(singles), 3)

    # get_valid_takes() — sum matches

    def test_sum_match(self):
        """Two table cards whose table_values sum to played hand_value."""
        played = Card("Hearts", "9")
        table = [Card("Clubs", "4"), Card("Diamonds", "5"), Card("Hearts", "2")]
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        self.assertIn(frozenset({Card("Clubs", "4"), Card("Diamonds", "5")}), takes)

    def test_multiple_valid_subsets_returned(self):
        """Both single-card and sum-match subsets are returned."""
        played = Card("Hearts", "6")
        table = [Card("Clubs", "6"), Card("Diamonds", "2"), Card("Hearts", "4")]
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        self.assertIn(frozenset({Card("Clubs", "6")}), takes)
        self.assertIn(frozenset({Card("Diamonds", "2"), Card("Hearts", "4")}), takes)

    # get_valid_takes() — special card hand values (Ace=14, Diamond-10=16, Spade-2=15)

    def test_ace_hand_value_used_as_target(self):
        """Ace played from hand targets 14, not 1."""
        played = Card("Hearts", "A")  # hand_value = 14
        table = [Card("Clubs", "7"), Card("Diamonds", "7")]  # 7+7=14
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        self.assertIn(frozenset({Card("Clubs", "7"), Card("Diamonds", "7")}), takes)

    def test_ace_table_value_is_1(self):
        """Ace on table contributes 1 to sums."""
        played = Card("Hearts", "8")  # hand_value = 8
        table = [Card("Spades", "A"), Card("Clubs", "7")]  # 1+7=8
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        self.assertIn(frozenset({Card("Spades", "A"), Card("Clubs", "7")}), takes)

    def test_diamond_10_hand_value_as_target(self):
        """Diamond-10 played targets 16."""
        played = Card("Diamonds", "10")  # hand_value = 16
        table = [Card("Clubs", "9"), Card("Hearts", "7")]  # 9+7=16
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        self.assertIn(frozenset({Card("Clubs", "9"), Card("Hearts", "7")}), takes)

    def test_spade_2_hand_value_as_target(self):
        """Spade-2 played targets 15."""
        played = Card("Spades", "2")  # hand_value = 15
        table = [Card("Clubs", "8"), Card("Hearts", "7")]  # 8+7=15
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        self.assertIn(frozenset({Card("Clubs", "8"), Card("Hearts", "7")}), takes)

    # get_valid_takes() — rules examples (casino_card_game.md)

    def test_rules_example_queen_valid_takes(self):
        """Queen of hearts (12) vs example table — two valid subsets."""
        played = Card("Hearts", "Q")  # hand_value = 12
        table = [
            Card("Diamonds", "6"),
            Card("Clubs", "5"),
            Card("Hearts", "J"),   # table_value 11
            Card("Spades", "A"),   # table_value 1
            Card("Clubs", "10"),
            Card("Clubs", "3"),
        ]
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        # J♥(11) + A♠(1) = 12
        self.assertIn(frozenset({Card("Hearts", "J"), Card("Spades", "A")}), takes)
        # D6(6) + C5(5) + A♠(1) = 12
        self.assertIn(frozenset({Card("Diamonds", "6"), Card("Clubs", "5"), Card("Spades", "A")}), takes)

    def test_rules_example_jack_valid_takes(self):
        """Jack of spades (11) vs example table — three valid subsets."""
        played = Card("Spades", "J")  # hand_value = 11
        table = [
            Card("Diamonds", "6"),
            Card("Clubs", "5"),
            Card("Hearts", "J"),   # table_value 11
            Card("Spades", "A"),   # table_value 1
            Card("Clubs", "10"),
            Card("Clubs", "3"),
        ]
        takes = CasinoTakeAlgorithm.get_valid_takes(played, table)
        # D6(6) + C5(5) = 11
        self.assertIn(frozenset({Card("Diamonds", "6"), Card("Clubs", "5")}), takes)
        # J♥(11) = 11
        self.assertIn(frozenset({Card("Hearts", "J")}), takes)
        # C10(10) + A♠(1) = 11
        self.assertIn(frozenset({Card("Clubs", "10"), Card("Spades", "A")}), takes)

    # is_valid_take()

    def test_is_valid_take_single_subset(self):
        played = Card("Hearts", "7")
        table = [Card("Clubs", "7"), Card("Diamonds", "3")]
        self.assertTrue(
            CasinoTakeAlgorithm.is_valid_take(
                played, frozenset({Card("Clubs", "7")}), table
            )
        )

    def test_is_valid_take_multi_subset(self):
        """Taking all 5 cards at once via three non-overlapping valid subsets."""
        played = Card("Spades", "J")  # hand_value = 11
        table = [
            Card("Diamonds", "6"),
            Card("Clubs", "5"),
            Card("Hearts", "J"),
            Card("Spades", "A"),
            Card("Clubs", "10"),
        ]
        # {D6+C5}=11, {J♥}=11, {C10+A♠}=11 — all non-overlapping
        chosen = frozenset(table)
        self.assertTrue(CasinoTakeAlgorithm.is_valid_take(played, chosen, table))

    def test_is_valid_take_empty_is_false(self):
        played = Card("Hearts", "7")
        table = [Card("Clubs", "7")]
        self.assertFalse(CasinoTakeAlgorithm.is_valid_take(played, frozenset(), table))

    def test_is_valid_take_card_not_on_table_is_false(self):
        played = Card("Hearts", "7")
        table = [Card("Clubs", "3")]
        off_table = frozenset({Card("Spades", "7")})
        self.assertFalse(CasinoTakeAlgorithm.is_valid_take(played, off_table, table))

    def test_is_valid_take_wrong_sum_is_false(self):
        played = Card("Hearts", "7")
        table = [Card("Clubs", "3"), Card("Diamonds", "5")]
        # 3+5=8 ≠ 7
        self.assertFalse(
            CasinoTakeAlgorithm.is_valid_take(
                played,
                frozenset({Card("Clubs", "3"), Card("Diamonds", "5")}),
                table,
            )
        )


class TestDeckCasinoGame(unittest.TestCase):
    """Tests for DeckCasinoGame setup, turns, sweep detection, and scoring."""

    # Initialisation

    def test_one_player_raises(self):
        with self.assertRaises(ValueError):
            DeckCasinoGame([Player("Solo")])

    # start_game()

    def test_start_game_deals_4_to_table(self):
        game, _ = make_game()
        self.assertEqual(len(game.table_cards), 4)

    def test_start_game_deals_4_to_each_player(self):
        game, players = make_game(("Alice", "Bob", "Carol"))
        for p in players:
            self.assertEqual(p.hand.card_count(), 4)

    def test_start_game_stock_correct_size_two_players(self):
        # 52 - 4 (table) - 4*2 (players) = 40
        game, _ = make_game(("Alice", "Bob"))
        self.assertEqual(len(game.deck), 40)

    def test_start_game_resets_last_taker(self):
        game, _ = make_game()
        self.assertIsNone(game._last_taker)

    def test_start_game_turn_index_zero(self):
        game, players = make_game()
        self.assertIs(game.current_player, players[0])

    # play_card() — place

    def test_play_card_place_removes_from_hand(self):
        game, players = make_game()
        card = Card("Hearts", "3")
        inject_state(game, players[0], [card], [Card("Clubs", "5")])
        count_before = players[0].hand.card_count()  # 1, captured after inject
        game.play_card(card)
        # hand loses 1 (played), then replenishes 1 from stock → net 0
        self.assertEqual(players[0].hand.card_count(), count_before)

    def test_play_card_place_adds_to_table(self):
        game, players = make_game()
        card = Card("Hearts", "3")
        inject_state(game, players[0], [card], [Card("Clubs", "5")])
        game.play_card(card)
        self.assertIn(card, game.table_cards)

    # play_card() — take

    def test_play_card_take_removes_from_table(self):
        game, players = make_game()
        played = Card("Hearts", "7")
        target = Card("Clubs", "7")
        inject_state(game, players[0], [played], [target, Card("Diamonds", "3")])
        game.play_card(played, frozenset({target}))
        self.assertNotIn(target, game.table_cards)

    def test_play_card_take_adds_played_and_taken_to_collection(self):
        game, players = make_game()
        played = Card("Hearts", "7")
        target = Card("Clubs", "7")
        inject_state(game, players[0], [played], [target])
        game.play_card(played, frozenset({target}))
        self.assertIn(played, players[0].collection)
        self.assertIn(target, players[0].collection)

    def test_play_card_replenishes_hand_from_stock(self):
        game, players = make_game()
        played = Card("Hearts", "3")
        inject_state(game, players[0], [played], [Card("Clubs", "5")])
        stock_before = len(game.deck)
        game.play_card(played)
        # Stock decreases by 1, hand stays at 1 (lost 1, gained 1)
        self.assertEqual(len(game.deck), stock_before - 1)
        self.assertEqual(players[0].hand.card_count(), 1)

    # play_card() — ValueError cases

    def test_play_card_invalid_take_raises(self):
        game, players = make_game()
        played = Card("Hearts", "7")
        wrong = Card("Clubs", "3")  # 3 ≠ 7
        inject_state(game, players[0], [played], [wrong])
        with self.assertRaises(ValueError):
            game.play_card(played, frozenset({wrong}))

    def test_play_card_not_in_hand_raises(self):
        game, players = make_game()
        not_held = Card("Spades", "K")
        inject_state(game, players[0], [Card("Hearts", "3")], [Card("Clubs", "5")])
        with self.assertRaises(ValueError):
            game.play_card(not_held)

    # advance_turn()

    def test_advance_turn_cycles_through_players(self):
        game, players = make_game(("Alice", "Bob", "Carol"))
        game.advance_turn()
        self.assertIs(game.current_player, players[1])
        game.advance_turn()
        self.assertIs(game.current_player, players[2])
        game.advance_turn()
        self.assertIs(game.current_player, players[0])

    # check_sweep() — sweep detection

    def test_check_sweep_awards_sweep_when_table_empty(self):
        game, players = make_game()
        played = Card("Hearts", "7")
        target = Card("Clubs", "7")
        inject_state(game, players[0], [played], [target])
        game.play_card(played, frozenset({target}))
        self.assertEqual(players[0].sweeps, 1)

    def test_check_sweep_not_awarded_when_table_not_empty(self):
        game, players = make_game()
        played = Card("Hearts", "7")
        target = Card("Clubs", "7")
        inject_state(game, players[0], [played], [target, Card("Diamonds", "3")])
        game.play_card(played, frozenset({target}))
        self.assertEqual(players[0].sweeps, 0)

    def test_multiple_sweeps_accumulated(self):
        game, players = make_game()
        # First sweep
        played1 = Card("Hearts", "7")
        target1 = Card("Clubs", "7")
        inject_state(game, players[0], [played1], [target1])
        game.play_card(played1, frozenset({target1}))
        # Second sweep (advance back to players[0])
        game.advance_turn()
        played2 = Card("Diamonds", "5")
        target2 = Card("Spades", "5")
        inject_state(game, players[0], [played2], [target2])
        game.play_card(played2, frozenset({target2}))
        self.assertEqual(players[0].sweeps, 2)

    # is_round_over()

    def test_is_round_over_false_after_start(self):
        game, _ = make_game()
        self.assertFalse(game.is_round_over())

    # end_round()

    def test_end_round_gives_remaining_table_to_last_taker(self):
        game, players = make_game()
        leftover = Card("Diamonds", "9")
        game._table_cards = [leftover]
        game._last_taker = players[0]
        game._deck._cards.clear()
        for p in players:
            for c in list(p.hand.cards):
                p.hand.remove_card(c)
        game.end_round()
        self.assertIn(leftover, players[0].collection)

    def test_end_round_calls_calculate_scores(self):
        """Scores must change after end_round (at minimum sweeps are processed)."""
        game, players = make_game()
        players[0].add_sweep()
        game._table_cards = []
        game._last_taker = players[0]
        game._deck._cards.clear()
        for p in players:
            for c in list(p.hand.cards):
                p.hand.remove_card(c)
        game.end_round()
        self.assertGreater(players[0].total_score, 0)

    # calculate_scores() — point categories

    def test_calculate_scores_ace_gives_1_point_each(self):
        game, players = make_game()
        players[0].add_to_collection([Card("Hearts", "A"), Card("Spades", "A")])
        players[1].add_to_collection([Card("Clubs", "3")])
        game.calculate_scores()
        # 2 aces → +2 for players[0]; most cards → +1 for players[0]
        self.assertGreaterEqual(players[0].total_score, 2)

    def test_calculate_scores_most_cards_gives_1_point(self):
        game, players = make_game()
        # Hearts/Clubs/Diamonds only — avoids spade-bonus interference
        players[0].add_to_collection([Card("Hearts", "2"), Card("Clubs", "3"), Card("Diamonds", "4")])
        players[1].add_to_collection([Card("Hearts", "5")])
        score_before = players[0].total_score
        game.calculate_scores()
        self.assertGreaterEqual(players[0].total_score - score_before, 1)

    def test_calculate_scores_most_cards_tie_gives_no_point(self):
        game, players = make_game()
        players[0].add_to_collection([Card("Hearts", "2")])
        players[1].add_to_collection([Card("Clubs", "3")])
        before = [p.total_score for p in players]
        game.calculate_scores()
        gained = [players[i].total_score - before[i] for i in range(2)]
        self.assertNotIn(1, gained)

    def test_calculate_scores_most_spades_gives_2_points(self):
        game, players = make_game()
        players[0].add_to_collection([Card("Spades", "3"), Card("Spades", "4"), Card("Spades", "5")])
        players[1].add_to_collection([Card("Hearts", "2")])
        game.calculate_scores()
        self.assertGreaterEqual(players[0].total_score, 2)

    def test_calculate_scores_diamond_10_gives_2_points(self):
        game, players = make_game()
        # players[1] has more cards → most-cards point goes to players[1], isolating Diamond-10 bonus
        players[0].add_to_collection([Card("Diamonds", "10")])
        players[1].add_to_collection([Card("Hearts", "2"), Card("Clubs", "3"), Card("Hearts", "4")])
        score_before = players[0].total_score
        game.calculate_scores()
        self.assertGreaterEqual(players[0].total_score - score_before, 2)

    def test_calculate_scores_spade_2_gives_1_point(self):
        game, players = make_game()
        players[0].add_to_collection([Card("Spades", "2")])
        players[1].add_to_collection([Card("Clubs", "3")])
        score_before = players[0].total_score
        game.calculate_scores()
        self.assertGreaterEqual(players[0].total_score - score_before, 1)

    def test_calculate_scores_sweep_gives_1_point_each(self):
        game, players = make_game()
        players[0].add_sweep()
        players[0].add_sweep()
        game.calculate_scores()
        self.assertGreaterEqual(players[0].total_score, 2)

    # has_winner()

    def test_has_winner_false_at_start(self):
        game, _ = make_game()
        self.assertFalse(game.has_winner())

    def test_has_winner_true_at_16(self):
        game, players = make_game()
        players[0].add_score(16)
        self.assertTrue(game.has_winner())

    def test_has_winner_false_at_15(self):
        game, players = make_game()
        players[0].add_score(15)
        self.assertFalse(game.has_winner())


if __name__ == "__main__":
    unittest.main()
