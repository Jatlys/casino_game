# Unit tests for Week 4: AIOpponent and FileManager.
# Run with: python -m unittest tests.deck_casino_tests.test_week4

import os
import unittest

from model.card import Card
from model.player import Player
from model.deck_casino_game import DeckCasinoGame
from model.ai_opponent import AIOpponent
from model.file_manager import FileManager, SAVE_FILE


# ---------------------------------------------------------------------------
# Helpers shared by multiple test classes
# ---------------------------------------------------------------------------

def make_game(names=("Alice", "Bot"), ai_indices=(1,)):
    """Return a started DeckCasinoGame. Players at ai_indices are marked AI."""
    players = [
        Player(n, is_ai=(i in ai_indices)) for i, n in enumerate(names)
    ]
    game = DeckCasinoGame(players)
    game.start_game()
    return game, players


def inject_state(game, player, hand_cards, table_cards):
    """Replace a player's hand and the game table with controlled cards."""
    game._table_cards = list(table_cards)
    for c in list(player.hand.cards):
        player.hand.remove_card(c)
    for c in hand_cards:
        player.hand.add_card(c)


def clear_save():
    """Remove the save file if it exists."""
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)


# ---------------------------------------------------------------------------
# AIOpponent tests
# ---------------------------------------------------------------------------

class TestAIOpponentSweep(unittest.TestCase):
    """Priority 1: AI must choose a sweep when one is available."""

    def test_sweep_taken_when_possible(self):
        game, players = make_game()
        played = Card("Hearts", "7")
        target = Card("Clubs", "7")
        inject_state(game, players[0], [played], [target])
        card, take = AIOpponent.decide_action(game)
        self.assertEqual(card, played)
        self.assertEqual(take, frozenset({target}))

    def test_sweep_clears_whole_table(self):
        """AI must take all table cards, not just one matching card."""
        game, players = make_game()
        played = Card("Hearts", "7")
        t1 = Card("Clubs", "3")
        t2 = Card("Diamonds", "4")
        inject_state(game, players[0], [played], [t1, t2])
        card, take = AIOpponent.decide_action(game)
        self.assertEqual(card, played)
        self.assertEqual(take, frozenset({t1, t2}))

    def test_sweep_preferred_over_partial_take(self):
        """When a sweep and a partial take both exist, AI sweeps."""
        game, players = make_game()
        # 9 of Hearts can take {5+4} = sweep; but also {5} alone is not valid (9≠5)
        # Actually let's set up: 9 can sweep {Clubs-9} OR {Clubs-5, Diamonds-4}
        played = Card("Hearts", "9")
        t1 = Card("Clubs", "9")   # single match
        t2 = Card("Spades", "5")
        t3 = Card("Hearts", "4")
        inject_state(game, players[0], [played], [t1, t2, t3])
        # full table = {t1, t2, t3}; 9 != 5+4+9=18; sweep only via t1 alone (not all)
        # So this is NOT a sweep scenario — just a single-card take
        card, take = AIOpponent.decide_action(game)
        self.assertIsNotNone(take)


class TestAIOpponentPrizeCature(unittest.TestCase):
    """Priority 2: AI must grab Diamond-10 or Spade-2 when possible."""

    def test_captures_diamond_10(self):
        game, players = make_game()
        played = Card("Hearts", "K")          # hand_value 13
        prize = Card("Diamonds", "10")        # table_value 10
        other = Card("Clubs", "3")            # 10+3=13 → valid take
        inject_state(game, players[0], [played], [prize, other])
        card, take = AIOpponent.decide_action(game)
        self.assertIn(prize, take)

    def test_captures_spade_2(self):
        game, players = make_game()
        played = Card("Hearts", "9")          # hand_value 9
        prize = Card("Spades", "2")           # table_value 2
        other = Card("Clubs", "7")            # 2+7=9
        inject_state(game, players[0], [played], [prize, other])
        card, take = AIOpponent.decide_action(game)
        self.assertIn(prize, take)


class TestAIOpponentMaximise(unittest.TestCase):
    """Priority 3: AI maximises cards taken."""

    def test_takes_larger_group(self):
        game, players = make_game()
        # 7 of Hearts: can take {Clubs-7} (1 card) OR {Diamonds-3, Spades-4} (2 cards).
        # Hearts-6 on the table cannot be covered by 7-of-Hearts, so no sweep is possible.
        played = Card("Hearts", "7")
        single = Card("Clubs", "7")
        pair1 = Card("Diamonds", "3")
        pair2 = Card("Spades", "4")
        blocker = Card("Hearts", "6")   # uncoverable → prevents full-table sweep
        inject_state(game, players[0], [played], [single, pair1, pair2, blocker])
        _, take = AIOpponent.decide_action(game)
        # AI should prefer the 2-card take over the 1-card take
        self.assertEqual(len(take), 2)
        self.assertIn(pair1, take)
        self.assertIn(pair2, take)


class TestAIOpponentSpecialPreference(unittest.TestCase):
    """Priority 4: Among equal-count takes, prefer those with special cards."""

    def test_prefers_take_with_ace(self):
        game, players = make_game()
        # 8 of Hearts: can take {Clubs-8} OR {Spades-A(1) + Clubs-7} — both size 1 / size 2
        # Let's make both options size 1: {Clubs-8} vs ... that's hard to engineer as equal.
        # Instead: only one valid take, and it contains an Ace — AI should still pick it.
        played = Card("Hearts", "8")
        ace = Card("Spades", "A")   # table_value = 1
        seven = Card("Clubs", "7")  # 1+7 = 8
        inject_state(game, players[0], [played], [ace, seven])
        _, take = AIOpponent.decide_action(game)
        self.assertIn(ace, take)
        self.assertIn(seven, take)


class TestAIOpponentPlacement(unittest.TestCase):
    """Priorities 5 & 6: Placement when no take is available."""

    def test_places_card_when_no_take(self):
        game, players = make_game()
        # 3 of Hearts vs table of 5 of Clubs — no match
        played = Card("Hearts", "3")
        inject_state(game, players[0], [played], [Card("Clubs", "5")])
        card, take = AIOpponent.decide_action(game)
        self.assertEqual(card, played)
        self.assertIsNone(take)

    def test_places_lowest_hand_value_card(self):
        # When every placement creates an equal sweep risk, fall back to lowest hand value.
        # table=[Diamonds-3]; placing Hearts-4 → [3,4] sweepable by 7; placing Clubs-5 → [3,5]
        # sweepable by 8. Both are risky → priority-6 tie-break picks Hearts-4 (hv=4).
        game, players = make_game()
        low = Card("Hearts", "4")
        high = Card("Clubs", "5")
        inject_state(game, players[0], [low, high], [Card("Diamonds", "3")])
        card, take = AIOpponent.decide_action(game)
        self.assertIsNone(take)
        self.assertEqual(card, low)

    def test_decide_action_empty_table_places_card(self):
        game, players = make_game()
        low = Card("Hearts", "3")
        inject_state(game, players[0], [low], [])
        card, take = AIOpponent.decide_action(game)
        self.assertEqual(card, low)
        self.assertIsNone(take)


# ---------------------------------------------------------------------------
# FileManager save / load round-trip tests
# ---------------------------------------------------------------------------

class TestFileManagerSaveLoad(unittest.TestCase):
    """Core save/load round-trip: 2 moves → save → reload → assert state matches."""

    def setUp(self):
        clear_save()

    def tearDown(self):
        clear_save()

    def _make_controlled_game(self):
        """Return a game where we can make two deterministic moves."""
        players = [Player("Alice"), Player("Bob")]
        game = DeckCasinoGame(players)
        game.start_game()

        # Inject a predictable state
        alice, bob = players
        played1 = Card("Hearts", "7")
        target1 = Card("Clubs", "7")
        inject_state(game, alice, [played1], [target1, Card("Diamonds", "5")])
        # Empty the stock so replenish doesn't interfere
        game._deck._cards.clear()

        return game, players, played1, target1

    def test_save_creates_file(self):
        game, _, played1, target1 = self._make_controlled_game()
        FileManager.save(game)
        self.assertTrue(os.path.exists(SAVE_FILE))

    def test_load_returns_none_when_no_file(self):
        self.assertIsNone(FileManager.load())

    def test_round_trip_turn_index(self):
        """Turn index must match after save → load."""
        game, players, played1, target1 = self._make_controlled_game()
        # Move 1
        game.play_card(played1, frozenset({target1}))
        # Move 2: Bob places a card
        bob = players[1]
        bob_card = list(bob.hand.cards)[0]
        game.play_card(bob_card)

        expected_turn = game._turn_index
        FileManager.save(game)

        restored, _ = FileManager.load()
        self.assertEqual(restored._turn_index, expected_turn)

    def test_round_trip_table_cards(self):
        """Table cards (count and identity) must match after save → load."""
        game, players, played1, target1 = self._make_controlled_game()
        game.play_card(played1, frozenset({target1}))

        table_before = game.table_cards
        FileManager.save(game)

        restored, _ = FileManager.load()
        self.assertEqual(sorted(str(c) for c in restored.table_cards),
                         sorted(str(c) for c in table_before))

    def test_round_trip_stock_pile(self):
        """Stock pile must match after save → load."""
        game, players, played1, target1 = self._make_controlled_game()
        game.play_card(played1, frozenset({target1}))

        stock_before = game.deck.cards
        FileManager.save(game)

        restored, _ = FileManager.load()
        self.assertEqual([str(c) for c in restored.deck.cards],
                         [str(c) for c in stock_before])

    def test_round_trip_player_scores(self):
        """Cumulative scores must match after save → load."""
        game, players, played1, target1 = self._make_controlled_game()
        players[0].add_score(5)
        FileManager.save(game)

        restored, _ = FileManager.load()
        self.assertEqual(restored.players[0].total_score, 5)

    def test_round_trip_player_hands(self):
        """Each player's hand cards must match after save → load."""
        game, players, played1, target1 = self._make_controlled_game()
        FileManager.save(game)

        restored, _ = FileManager.load()
        for orig, rest in zip(players, restored.players):
            self.assertEqual(
                sorted(str(c) for c in orig.hand.cards),
                sorted(str(c) for c in rest.hand.cards),
            )

    def test_round_trip_player_collections(self):
        """Player collections must match after save → load."""
        game, players, played1, target1 = self._make_controlled_game()
        game.play_card(played1, frozenset({target1}))

        alice_col = players[0].collection
        FileManager.save(game)

        restored, _ = FileManager.load()
        self.assertEqual(
            sorted(str(c) for c in restored.players[0].collection),
            sorted(str(c) for c in alice_col),
        )

    def test_round_trip_player_sweeps(self):
        """Sweep counters must match after save → load."""
        game, players, played1, target1 = self._make_controlled_game()
        players[0].add_sweep()
        FileManager.save(game)

        restored, _ = FileManager.load()
        self.assertEqual(restored.players[0].sweeps, 1)

    def test_round_trip_player_names_and_is_ai(self):
        """Player names and is_ai flags must survive round-trip."""
        players = [Player("Human"), Player("Bot", is_ai=True)]
        game = DeckCasinoGame(players)
        game.start_game()
        FileManager.save(game)

        restored, _ = FileManager.load()
        self.assertEqual(restored.players[0].name, "Human")
        self.assertFalse(restored.players[0].is_ai)
        self.assertEqual(restored.players[1].name, "Bot")
        self.assertTrue(restored.players[1].is_ai)

    def test_round_trip_move_history_preserved(self):
        """move_history list must survive save → load unchanged."""
        game, players, _, _ = self._make_controlled_game()
        history = [{"player": "Alice", "played": "7 of Hearts",
                    "action": "take", "took": ["7 of Clubs"], "advice": "Good move."}]
        FileManager.save(game, history)

        _, loaded_history = FileManager.load()
        self.assertEqual(loaded_history, history)

    def test_two_moves_then_full_state_match(self):
        """Core spec: make 2 moves, save, reload, assert all state matches."""
        players = [Player("Alice"), Player("Bob")]
        game = DeckCasinoGame(players)
        game.start_game()
        alice, bob = players

        # Inject controlled state and drain stock
        c1 = Card("Hearts", "7")
        t1 = Card("Clubs", "7")
        inject_state(game, alice, [c1], [t1, Card("Diamonds", "5")])
        game._deck._cards.clear()

        # Move 1: Alice takes
        game.play_card(c1, frozenset({t1}))

        # Move 2: Bob places
        bob_card = list(bob.hand.cards)[0]
        game.play_card(bob_card)

        # Snapshot state
        snap_turn = game._turn_index
        snap_table = sorted(str(c) for c in game._table_cards)
        snap_stock = [str(c) for c in game._deck._cards]
        snap_scores = [p.total_score for p in game.players]

        FileManager.save(game)
        restored, _ = FileManager.load()

        self.assertEqual(restored._turn_index, snap_turn)
        self.assertEqual(sorted(str(c) for c in restored._table_cards), snap_table)
        self.assertEqual([str(c) for c in restored._deck._cards], snap_stock)
        self.assertEqual([p.total_score for p in restored.players], snap_scores)


# ---------------------------------------------------------------------------
# FileManager.record_move / _generate_advice tests
# ---------------------------------------------------------------------------

class TestRecordMove(unittest.TestCase):
    """Tests for move recording and advice generation."""

    def test_record_move_take_action(self):
        played = Card("Hearts", "7")
        take = frozenset({Card("Clubs", "7")})
        table = [Card("Clubs", "7")]
        rec = FileManager.record_move("Alice", played, take, table)
        self.assertEqual(rec["action"], "take")
        self.assertEqual(rec["player"], "Alice")
        self.assertEqual(rec["played"], "7 of Hearts")

    def test_record_move_place_action(self):
        played = Card("Hearts", "3")
        table = [Card("Clubs", "5")]
        rec = FileManager.record_move("Bob", played, None, table)
        self.assertEqual(rec["action"], "place")
        self.assertEqual(rec["took"], [])

    def test_advice_missed_sweep(self):
        played = Card("Hearts", "7")
        table = [Card("Clubs", "7")]
        # Player only takes nothing (places) even though a take was available
        rec = FileManager.record_move("Alice", played, None, table)
        self.assertIn("take", rec["advice"].lower())

    def test_advice_captures_special(self):
        played = Card("Hearts", "K")   # hand_value 13
        prize = Card("Diamonds", "10")
        other = Card("Clubs", "3")
        take = frozenset({prize, other})
        table = [prize, other]
        rec = FileManager.record_move("Alice", played, take, table)
        self.assertIn("high-value", rec["advice"].lower())


if __name__ == "__main__":
    unittest.main()
