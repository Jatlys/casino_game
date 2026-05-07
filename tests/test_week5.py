"""Week 5 unit tests: Hand.blackjack_value, BettingSystem, BaccaratGame."""

import unittest

from model.card import Card
from model.hand import Hand
from model.player import Player
from model.betting_system import BettingSystem
from model.blackjack_game import AIDealer, BlackjackGame
from model.baccarat_game import BaccaratGame, _baccarat_hand_total


# ===========================================================================
# Hand.blackjack_value()
# ===========================================================================

def _make_hand(*pairs: tuple[str, str]) -> Hand:
    """Helper: build a Hand from (suit, rank) pairs."""
    h = Hand()
    for suit, rank in pairs:
        h.add_card(Card(suit, rank))
    return h


class TestBlackjackValue(unittest.TestCase):
    def test_ace_plus_10_is_21(self):
        h = _make_hand(("Hearts", "A"), ("Spades", "10"))
        self.assertEqual(h.blackjack_value(), 21)

    def test_ace_plus_5_plus_7_is_13(self):
        # Ace demoted from 11 to 1 → 1+5+7 = 13
        h = _make_hand(("Hearts", "A"), ("Hearts", "5"), ("Hearts", "7"))
        self.assertEqual(h.blackjack_value(), 13)

    def test_5_5_5_7_is_bust(self):
        h = _make_hand(("Hearts", "5"), ("Diamonds", "5"),
                       ("Clubs", "5"), ("Spades", "7"))
        self.assertEqual(h.blackjack_value(), 22)  # > 21 → bust

    def test_face_cards_count_as_10(self):
        h = _make_hand(("Hearts", "K"), ("Spades", "Q"))
        self.assertEqual(h.blackjack_value(), 20)

    def test_two_aces_one_demoted(self):
        # 11+11 = 22 → demote one → 12
        h = _make_hand(("Hearts", "A"), ("Spades", "A"))
        self.assertEqual(h.blackjack_value(), 12)

    def test_soft_17(self):
        # Ace + 6 = 17 (soft)
        h = _make_hand(("Hearts", "A"), ("Clubs", "6"))
        self.assertEqual(h.blackjack_value(), 17)

    def test_natural_blackjack_ace_king(self):
        h = _make_hand(("Diamonds", "A"), ("Clubs", "K"))
        self.assertEqual(h.blackjack_value(), 21)

    def test_empty_hand_is_zero(self):
        h = Hand()
        self.assertEqual(h.blackjack_value(), 0)

    def test_number_cards_sum_correctly(self):
        h = _make_hand(("Hearts", "3"), ("Diamonds", "4"), ("Clubs", "9"))
        self.assertEqual(h.blackjack_value(), 16)

    def test_jack_queen_king_all_ten(self):
        for rank in ("J", "Q", "K"):
            with self.subTest(rank=rank):
                h = _make_hand(("Hearts", rank), ("Spades", "5"))
                self.assertEqual(h.blackjack_value(), 15)


# ===========================================================================
# BettingSystem
# ===========================================================================

class TestBettingSystemValidation(unittest.TestCase):
    def test_zero_bet_raises(self):
        with self.assertRaisesRegex(ValueError, "greater than 0"):
            BettingSystem.validate_bet(0, 500)

    def test_negative_bet_raises(self):
        with self.assertRaises(ValueError):
            BettingSystem.validate_bet(-10, 500)

    def test_bet_exceeds_bankroll_raises(self):
        with self.assertRaisesRegex(ValueError, "exceeds bankroll"):
            BettingSystem.validate_bet(501, 500)

    def test_exact_bankroll_bet_is_valid(self):
        BettingSystem.validate_bet(500, 500)   # no exception

    def test_normal_bet_is_valid(self):
        BettingSystem.validate_bet(100, 500)   # no exception


class TestBlackjackPayout(unittest.TestCase):
    def test_natural_payout(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "natural", "blackjack"), 250)

    def test_win_payout(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "win", "blackjack"), 200)

    def test_push_returns_bet(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "push", "blackjack"), 100)

    def test_bust_payout_is_zero(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "bust", "blackjack"), 0)

    def test_lose_payout_is_zero(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "lose", "blackjack"), 0)


class TestBaccaratPayout(unittest.TestCase):
    def test_punto_win_punto_bet(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "punto_win", "baccarat", "punto"), 200)

    def test_banco_win_banco_bet(self):
        payout = BettingSystem.calculate_payout(100, "banco_win", "baccarat", "banco")
        self.assertEqual(payout, 195)   # 5% commission

    def test_tie_tie_bet(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "tie", "baccarat", "tie"), 900)

    def test_tie_punto_bet_is_push(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "tie", "baccarat", "punto"), 100)

    def test_tie_banco_bet_is_push(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "tie", "baccarat", "banco"), 100)

    def test_punto_win_banco_bet_loses(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "punto_win", "baccarat", "banco"), 0)

    def test_banco_win_punto_bet_loses(self):
        self.assertEqual(BettingSystem.calculate_payout(100, "banco_win", "baccarat", "punto"), 0)


# ===========================================================================
# BaccaratGame — natural rule
# ===========================================================================

class TestBaccaratNatural(unittest.TestCase):
    def _make_deck(self, cards: list[Card]):
        """Build a Deck stub that yields cards in the given order."""
        from model.deck import Deck
        deck = object.__new__(Deck)
        deck._cards = list(reversed(cards))   # deal() pops from the end
        return deck

    def test_natural_9_no_third_card(self):
        # Deal order: Punto, Banco, Punto, Banco
        # Punto: 5+4=9, Banco: 3+2=5 → Punto natural
        cards = [
            Card("Hearts", "5"), Card("Clubs", "3"),
            Card("Hearts", "4"), Card("Clubs", "2"),
        ]
        player = Player("Tester", bankroll=1000)
        game = BaccaratGame(player)
        game.start_round(100, "punto", deck=self._make_deck(cards))
        self.assertTrue(game.natural)
        self.assertEqual(game.phase, "done")
        self.assertEqual(game.punto_total(), 9)

    def test_natural_8_banco(self):
        # Punto: 2+3=5, Banco: 4+4=8 → Banco natural
        cards = [
            Card("Hearts", "2"), Card("Clubs", "4"),
            Card("Hearts", "3"), Card("Clubs", "4"),
        ]
        player = Player("Tester", bankroll=1000)
        game = BaccaratGame(player)
        game.start_round(100, "banco", deck=self._make_deck(cards))
        self.assertTrue(game.natural)
        self.assertEqual(game.banco_total(), 8)
        self.assertEqual(game.phase, "done")

    def test_no_natural_phase_is_drawing(self):
        # Punto: 3+2=5, Banco: 4+3=7 → no natural
        cards = [
            Card("Hearts", "3"), Card("Clubs", "4"),
            Card("Hearts", "2"), Card("Clubs", "3"),
        ]
        player = Player("Tester", bankroll=1000)
        game = BaccaratGame(player)
        game.start_round(100, "punto", deck=self._make_deck(cards))
        self.assertFalse(game.natural)
        self.assertEqual(game.phase, "drawing")

    def test_draw_third_card_changes_phase_to_done(self):
        # Punto 5, Banco 7 — Punto draws (total 5 <= 5)
        cards = [
            Card("Hearts", "3"), Card("Clubs", "4"),
            Card("Hearts", "2"), Card("Clubs", "3"),
            Card("Spades", "6"),   # Punto's third card
        ]
        player = Player("Tester", bankroll=1000)
        game = BaccaratGame(player)
        game.start_round(100, "punto", deck=self._make_deck(cards))
        game.draw_third_card()
        self.assertEqual(game.phase, "done")

    def test_cannot_draw_after_natural(self):
        cards = [
            Card("Hearts", "5"), Card("Clubs", "3"),
            Card("Hearts", "4"), Card("Clubs", "2"),
        ]
        player = Player("Tester", bankroll=1000)
        game = BaccaratGame(player)
        game.start_round(100, "punto", deck=self._make_deck(cards))
        with self.assertRaises(RuntimeError):
            game.draw_third_card()

    def test_outcome_punto_wins(self):
        # Punto: 4+3=7, Banco: 3+3=6 → drawing phase (no natural), then Punto wins
        cards = [
            Card("Hearts", "4"), Card("Clubs", "3"),
            Card("Hearts", "3"), Card("Clubs", "3"),
            Card("Spades", "2"),   # extra card in case needed
        ]
        player = Player("Tester", bankroll=1000)
        game = BaccaratGame(player)
        game.start_round(100, "punto", deck=self._make_deck(cards))
        self.assertEqual(game.phase, "drawing")
        game.draw_third_card()
        result = game.get_result()
        self.assertEqual(result["outcome"], "punto_win")


# ===========================================================================
# BlackjackGame — basic smoke test
# ===========================================================================

class TestBlackjackGame(unittest.TestCase):
    def _make_deck(self, cards: list[Card]):
        """Build a Deck stub that yields cards in the given order."""
        from model.deck import Deck
        deck = object.__new__(Deck)
        deck._cards = list(reversed(cards))
        return deck

    def test_start_round_deducts_bet(self):
        player = Player("Tester", bankroll=500)
        game = BlackjackGame(player)
        cards = [
            Card("Hearts", "5"), Card("Clubs", "2"),
            Card("Hearts", "6"), Card("Clubs", "3"),
            Card("Spades", "9"), Card("Diamonds", "5"),
        ]
        game.start_round(100, deck=self._make_deck(cards))
        self.assertEqual(game.player.bankroll, 400)   # 500 - 100

    def test_natural_blackjack_phase_done(self):
        cards = [
            Card("Spades", "A"), Card("Clubs", "2"),
            Card("Hearts", "K"), Card("Diamonds", "3"),
            Card("Hearts", "5"), Card("Clubs", "9"),
        ]
        player = Player("Tester", bankroll=500)
        game = BlackjackGame(player)
        game.start_round(100, deck=self._make_deck(cards))
        self.assertEqual(game.phase, "done")

    def test_hit_adds_card(self):
        # Player gets 5+6=11, dealer gets 2+3=5 → no natural
        cards = [
            Card("Hearts", "5"), Card("Clubs", "2"),
            Card("Hearts", "6"), Card("Clubs", "3"),
            Card("Spades", "4"),   # hit card for player
            Card("Diamonds", "9"), Card("Clubs", "8"),  # dealer hits
        ]
        player = Player("Tester", bankroll=500)
        game = BlackjackGame(player)
        game.start_round(100, deck=self._make_deck(cards))
        self.assertEqual(game.phase, "player")
        self.assertEqual(game.current_hand.card_count(), 2)
        game.hit()
        self.assertEqual(game.current_hand.card_count(), 3)

    def test_stand_triggers_dealer_play(self):
        # Player 9+8=17, dealer 2+3=5; dealer hits K(15), then 6(21)
        cards = [
            Card("Hearts", "9"), Card("Clubs", "2"),
            Card("Hearts", "8"), Card("Clubs", "3"),
            Card("Diamonds", "K"),
            Card("Clubs", "6"),
        ]
        player = Player("Tester", bankroll=500)
        game = BlackjackGame(player)
        game.start_round(100, deck=self._make_deck(cards))
        game.stand()
        self.assertEqual(game.phase, "done")

    def test_settle_bets_credits_win(self):
        # Player 9+8=17, dealer 6+7=13 then hits K=23 → bust → player wins
        cards = [
            Card("Hearts", "9"), Card("Clubs", "6"),
            Card("Hearts", "8"), Card("Clubs", "7"),
            Card("Diamonds", "K"),   # dealer 6+7+K=23 → bust
        ]
        player = Player("Tester", bankroll=500)
        game = BlackjackGame(player)
        game.start_round(100, deck=self._make_deck(cards))
        game.stand()
        game.settle_bets()
        self.assertEqual(game.player.bankroll, 600)  # 400 (after bet) + 200 payout

    def test_invalid_bet_raises(self):
        player = Player("P", bankroll=50)
        game = BlackjackGame(player)
        with self.assertRaises(ValueError):
            game.start_round(100)   # 100 > 50


# ===========================================================================
# AIDealer
# ===========================================================================

class TestAIDealer(unittest.TestCase):
    def test_should_hit_below_17(self):
        h = _make_hand(("Hearts", "8"), ("Clubs", "8"))   # 16
        self.assertTrue(AIDealer.should_hit(h))

    def test_should_not_hit_at_17(self):
        h = _make_hand(("Hearts", "9"), ("Clubs", "8"))   # 17
        self.assertFalse(AIDealer.should_hit(h))

    def test_basic_strategy_soft_16_vs_9_hits(self):
        # player 16, dealer upcard 9 → hit
        self.assertEqual(AIDealer.basic_strategy_action(16, 9), "hit")

    def test_basic_strategy_20_vs_anything_stands(self):
        for upcard in range(2, 12):
            with self.subTest(upcard=upcard):
                self.assertEqual(AIDealer.basic_strategy_action(20, upcard), "stand")


if __name__ == "__main__":
    unittest.main()
