# Unit tests for Card, Deck, Hand, Player.
# Run with: python -m unittest tests/deck_casino/test_deck_casino.py
# Ref: project plan Section 7 (104083758_casino_project_plan.pdf)

import unittest

from model.card import Card
from model.deck import Deck
from model.hand import Hand
from model.player import Player


class TestCard(unittest.TestCase):
    """Tests for Card value methods, special detection, equality, and validation."""

    # Special card values (Ace=14/1, Diamond-10=16/10, Spade-2=15/2)

    def test_ace_hand_value(self):
        self.assertEqual(Card("Hearts", "A").hand_value(), 14)

    def test_ace_table_value(self):
        self.assertEqual(Card("Hearts", "A").table_value(), 1)

    def test_diamond_10_hand_value(self):
        self.assertEqual(Card("Diamonds", "10").hand_value(), 16)

    def test_diamond_10_table_value(self):
        self.assertEqual(Card("Diamonds", "10").table_value(), 10)

    def test_spade_2_hand_value(self):
        self.assertEqual(Card("Spades", "2").hand_value(), 15)

    def test_spade_2_table_value(self):
        self.assertEqual(Card("Spades", "2").table_value(), 2)

    # Regular card values

    def test_regular_numeric_hand_values(self):
        cases = [
            ("Hearts",   "2",  2),
            ("Clubs",    "7",  7),
            ("Diamonds", "9",  9),
            ("Hearts",   "10", 10),
        ]
        for suit, rank, expected in cases:
            with self.subTest(card=f"{rank} of {suit}"):
                self.assertEqual(Card(suit, rank).hand_value(), expected)

    def test_face_card_hand_values(self):
        cases = [("Hearts", "J", 11), ("Clubs", "Q", 12), ("Spades", "K", 13)]
        for suit, rank, expected in cases:
            with self.subTest(card=f"{rank} of {suit}"):
                self.assertEqual(Card(suit, rank).hand_value(), expected)

    def test_regular_hand_and_table_values_match(self):
        """For non-special cards hand_value() and table_value() are always equal."""
        cases = [("Hearts", "5"), ("Clubs", "K"), ("Diamonds", "J"), ("Hearts", "10")]
        for suit, rank in cases:
            with self.subTest(card=f"{rank} of {suit}"):
                card = Card(suit, rank)
                self.assertEqual(card.hand_value(), card.table_value())

    # is_special()

    def test_is_special_ace_all_suits(self):
        for suit in ["Hearts", "Diamonds", "Clubs", "Spades"]:
            with self.subTest(suit=suit):
                self.assertTrue(Card(suit, "A").is_special())

    def test_is_special_diamond_10(self):
        self.assertTrue(Card("Diamonds", "10").is_special())

    def test_is_special_spade_2(self):
        self.assertTrue(Card("Spades", "2").is_special())

    def test_not_special_regular_cards(self):
        cases = [("Hearts", "7"), ("Clubs", "K"), ("Diamonds", "J"),
                 ("Hearts", "10"), ("Clubs", "2")]
        for suit, rank in cases:
            with self.subTest(card=f"{rank} of {suit}"):
                self.assertFalse(Card(suit, rank).is_special())

    # Equality and hashing

    def test_equal_cards(self):
        self.assertEqual(Card("Hearts", "7"), Card("Hearts", "7"))

    def test_unequal_different_suit(self):
        self.assertNotEqual(Card("Hearts", "7"), Card("Clubs", "7"))

    def test_unequal_different_rank(self):
        self.assertNotEqual(Card("Hearts", "7"), Card("Hearts", "8"))

    def test_equal_cards_have_same_hash(self):
        self.assertEqual(hash(Card("Hearts", "A")), hash(Card("Hearts", "A")))

    def test_card_usable_in_set(self):
        """Duplicate suit+rank should collapse to one entry in a set."""
        s = {Card("Hearts", "A"), Card("Hearts", "A"), Card("Clubs", "K")}
        self.assertEqual(len(s), 2)

    # __str__

    def test_str_format(self):
        self.assertEqual(str(Card("Spades", "K")), "K of Spades")

    # Validation

    def test_invalid_suit_raises(self):
        with self.assertRaises(ValueError):
            Card("Jokers", "A")

    def test_invalid_rank_raises(self):
        with self.assertRaises(ValueError):
            Card("Hearts", "1")


class TestDeck(unittest.TestCase):
    """Tests for Deck initialisation, deal(), shuffle(), and is_empty()."""

    # Initialisation

    def test_new_deck_has_52_cards(self):
        self.assertEqual(len(Deck().cards), 52)

    def test_new_deck_all_unique_cards(self):
        self.assertEqual(len(set(Deck().cards)), 52)

    # deal() — correct count reduction

    def test_deal_returns_list(self):
        self.assertIsInstance(Deck().deal(1), list)

    def test_deal_n_reduces_len_by_n(self):
        """After dealing n cards, len(deck.cards) == 52 - n."""
        for n in [1, 4, 13, 26, 52]:
            with self.subTest(n=n):
                deck = Deck()
                deck.deal(n)
                self.assertEqual(len(deck.cards), 52 - n)

    def test_dealt_cards_removed_from_deck(self):
        deck = Deck()
        dealt = deck.deal(4)
        for card in dealt:
            self.assertNotIn(card, deck.cards)

    def test_deal_returns_correct_count(self):
        self.assertEqual(len(Deck().deal(7)), 7)

    # deal() — ValueError cases

    def test_deal_from_empty_raises(self):
        deck = Deck()
        deck.deal(52)
        with self.assertRaises(ValueError):
            deck.deal(1)

    def test_deal_more_than_remaining_raises(self):
        with self.assertRaises(ValueError):
            Deck().deal(53)

    def test_deal_zero_raises(self):
        with self.assertRaises(ValueError):
            Deck().deal(0)

    # shuffle()

    def test_shuffle_preserves_count(self):
        deck = Deck()
        deck.shuffle()
        self.assertEqual(len(deck.cards), 52)

    def test_shuffle_preserves_card_set(self):
        """Every card present before shuffle must still be present after."""
        deck = Deck()
        before = set(deck.cards)
        deck.shuffle()
        self.assertEqual(set(deck.cards), before)

    # is_empty()

    def test_is_empty_false_on_new_deck(self):
        self.assertFalse(Deck().is_empty())

    def test_is_empty_true_after_dealing_all(self):
        deck = Deck()
        deck.deal(52)
        self.assertTrue(deck.is_empty())

    # __len__

    def test_len_matches_cards_list(self):
        deck = Deck()
        self.assertEqual(len(deck), len(deck.cards))


class TestHand(unittest.TestCase):
    """Tests for Hand mutation, query methods, and error handling."""

    # Initial state

    def test_new_hand_is_empty(self):
        self.assertTrue(Hand().is_empty())

    def test_new_hand_card_count_zero(self):
        self.assertEqual(Hand().card_count(), 0)

    def test_owner_stored_correctly(self):
        self.assertEqual(Hand(owner="Alice").owner, "Alice")

    # add_card / remove_card

    def test_add_card_increases_count(self):
        hand = Hand()
        hand.add_card(Card("Hearts", "7"))
        self.assertEqual(hand.card_count(), 1)

    def test_add_multiple_cards(self):
        hand = Hand()
        for rank in ["2", "5", "K"]:
            hand.add_card(Card("Hearts", rank))
        self.assertEqual(hand.card_count(), 3)

    def test_remove_card_decreases_count(self):
        hand = Hand()
        card = Card("Hearts", "7")
        hand.add_card(card)
        hand.remove_card(card)
        self.assertEqual(hand.card_count(), 0)

    def test_remove_absent_card_raises(self):
        with self.assertRaises(ValueError):
            Hand().remove_card(Card("Hearts", "7"))

    def test_cards_property_returns_copy(self):
        """Mutating the returned list must not affect the internal hand."""
        hand = Hand()
        hand.add_card(Card("Hearts", "7"))
        hand.cards.clear()
        self.assertEqual(hand.card_count(), 1)

    # get_value()

    def test_get_value_regular_cards(self):
        hand = Hand()
        hand.add_card(Card("Hearts", "5"))
        hand.add_card(Card("Clubs",  "3"))
        self.assertEqual(hand.get_value(), 8)

    def test_get_value_with_ace(self):
        """Ace contributes 14 to hand value."""
        hand = Hand()
        hand.add_card(Card("Hearts", "A"))
        hand.add_card(Card("Clubs",  "5"))
        self.assertEqual(hand.get_value(), 19)

    def test_get_value_with_diamond_10(self):
        """Diamond-10 contributes 16 to hand value."""
        hand = Hand()
        hand.add_card(Card("Diamonds", "10"))
        hand.add_card(Card("Hearts",   "3"))
        self.assertEqual(hand.get_value(), 19)

    def test_get_value_with_spade_2(self):
        """Spade-2 contributes 15 to hand value."""
        hand = Hand()
        hand.add_card(Card("Spades", "2"))
        hand.add_card(Card("Hearts", "4"))
        self.assertEqual(hand.get_value(), 19)

    def test_get_value_empty_hand(self):
        self.assertEqual(Hand().get_value(), 0)

    # __str__

    def test_str_empty_hand(self):
        self.assertEqual(str(Hand()), "(empty hand)")

    def test_str_contains_card_name(self):
        hand = Hand()
        hand.add_card(Card("Hearts", "A"))
        self.assertIn("A of Hearts", str(hand))


class TestPlayer(unittest.TestCase):
    """Tests for Player properties, scoring, collection, and round management."""

    # Initial state

    def test_name_stored(self):
        self.assertEqual(Player("Alice").name, "Alice")

    def test_is_ai_defaults_false(self):
        self.assertFalse(Player("Alice").is_ai)

    def test_is_ai_can_be_true(self):
        self.assertTrue(Player("Bot", is_ai=True).is_ai)

    def test_initial_score_zero(self):
        self.assertEqual(Player("Alice").total_score, 0)

    def test_initial_sweeps_zero(self):
        self.assertEqual(Player("Alice").sweeps, 0)

    def test_initial_collection_empty(self):
        self.assertEqual(len(Player("Alice").collection), 0)

    def test_player_has_hand_instance(self):
        self.assertIsInstance(Player("Alice").hand, Hand)

    def test_hand_owner_matches_player_name(self):
        self.assertEqual(Player("Alice").hand.owner, "Alice")

    # add_score / add_sweep

    def test_add_score_accumulates(self):
        p = Player("Alice")
        p.add_score(3)
        p.add_score(5)
        self.assertEqual(p.total_score, 8)

    def test_add_sweep_increments(self):
        p = Player("Alice")
        p.add_sweep()
        p.add_sweep()
        self.assertEqual(p.sweeps, 2)

    # add_to_collection()

    def test_add_single_card(self):
        p = Player("Alice")
        p.add_to_collection(Card("Hearts", "7"))
        self.assertEqual(len(p.collection), 1)

    def test_add_list_of_cards(self):
        p = Player("Alice")
        p.add_to_collection([Card("Hearts", "7"), Card("Clubs", "3")])
        self.assertEqual(len(p.collection), 2)

    def test_collection_property_returns_copy(self):
        """Mutating the returned list must not affect the internal collection."""
        p = Player("Alice")
        p.add_to_collection(Card("Hearts", "7"))
        p.collection.clear()
        self.assertEqual(len(p.collection), 1)

    # reset_for_round()

    def test_reset_clears_hand(self):
        p = Player("Alice")
        p.hand.add_card(Card("Hearts", "7"))
        p.reset_for_round()
        self.assertTrue(p.hand.is_empty())

    def test_reset_clears_collection(self):
        p = Player("Alice")
        p.add_to_collection(Card("Hearts", "7"))
        p.reset_for_round()
        self.assertEqual(len(p.collection), 0)

    def test_reset_clears_sweeps(self):
        p = Player("Alice")
        p.add_sweep()
        p.reset_for_round()
        self.assertEqual(p.sweeps, 0)

    def test_reset_preserves_total_score(self):
        """total_score must persist across rounds."""
        p = Player("Alice")
        p.add_score(7)
        p.reset_for_round()
        self.assertEqual(p.total_score, 7)


if __name__ == "__main__":
    unittest.main()
