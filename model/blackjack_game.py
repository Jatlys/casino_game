from model.card import Card
from model.deck import Deck
from model.hand import Hand
from model.player import Player
from model.betting_system import BettingSystem


# ---------------------------------------------------------------------------
# AIDealer
# ---------------------------------------------------------------------------

class AIDealer:
    """Encapsulates Blackjack dealer behaviour and basic-strategy reference.

    Dealer rule: hit on any total < 17; stand on 17+.

    Basic strategy table maps (player_total, dealer_upcard) to a recommended
    action string: "hit" | "stand" | "double" | "split".
    Dealer upcard is its numeric Blackjack value (Ace = 11).
    """

    # Condensed basic-strategy hard-total table.
    # Keys: (player_total, dealer_upcard_value)
    # Only hard totals are listed; soft totals and pairs handled separately.
    _HARD_STRATEGY: dict[tuple[int, int], str] = {}

    @classmethod
    def _build_strategy(cls) -> None:
        """Populate _HARD_STRATEGY with canonical basic-strategy decisions."""
        for player_total in range(4, 22):
            for upcard in range(2, 12):   # 2-10, Ace=11
                if player_total <= 8:
                    action = "hit"
                elif player_total == 9:
                    action = "double" if 3 <= upcard <= 6 else "hit"
                elif player_total == 10:
                    action = "double" if 2 <= upcard <= 9 else "hit"
                elif player_total == 11:
                    action = "double" if upcard != 11 else "hit"
                elif player_total == 12:
                    action = "stand" if 4 <= upcard <= 6 else "hit"
                elif player_total in (13, 14):
                    action = "stand" if 2 <= upcard <= 6 else "hit"
                elif player_total in (15, 16):
                    action = "stand" if 2 <= upcard <= 6 else "hit"
                else:  # 17+
                    action = "stand"
                cls._HARD_STRATEGY[(player_total, upcard)] = action

    @classmethod
    def basic_strategy_action(cls, player_total: int, dealer_upcard: int) -> str:
        """Return the basic-strategy recommended action.

        Args:
            player_total:  Player's current Blackjack hand value.
            dealer_upcard: Dealer's visible card Blackjack value (Ace = 11).

        Returns:
            "hit" | "stand" | "double"
        """
        if not cls._HARD_STRATEGY:
            cls._build_strategy()
        return cls._HARD_STRATEGY.get((player_total, dealer_upcard), "stand")

    @staticmethod
    def should_hit(hand: Hand) -> bool:
        """Return True if the dealer must hit (value < 17)."""
        return hand.blackjack_value() < 17


# ---------------------------------------------------------------------------
# BlackjackGame
# ---------------------------------------------------------------------------

class BlackjackGame:
    """One round of Blackjack: single human player vs. the AIDealer.

    Phases
    ──────
    "betting"  → waiting for start_round(bet) call
    "player"   → player actions (hit / stand / double_down / split)
    "dealer"   → dealer auto-plays after player stands
    "done"     → round over; call get_results() then settle_bets()

    Split support
    ─────────────
    self._hands  is a list of Hand objects (length > 1 after a split).
    self._bets   mirrors self._hands with the bet for each hand.
    self._current_hand_index points to the hand being played.
    """

    def __init__(self, player: Player, dealer_name: str = "Dealer") -> None:
        self._player = player
        self._dealer_name = dealer_name
        self._deck: Deck = Deck()
        self._hands: list[Hand] = []
        self._bets: list[int] = []
        self._dealer_hand: Hand = Hand(dealer_name)
        self._current_hand_index: int = 0
        self._phase: str = "betting"

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def player(self) -> Player:
        """The human player in this round."""
        return self._player

    @property
    def dealer_hand(self) -> Hand:
        """The dealer's current hand."""
        return self._dealer_hand

    @property
    def hands(self) -> list[Hand]:
        """All active player hands (length > 1 after a split)."""
        return list(self._hands)

    @property
    def bets(self) -> list[int]:
        """Bet amount for each hand, parallel to hands."""
        return list(self._bets)

    @property
    def current_hand(self) -> Hand:
        """The hand currently being played."""
        return self._hands[self._current_hand_index]

    @property
    def current_hand_index(self) -> int:
        """Index of the hand currently being played."""
        return self._current_hand_index

    @property
    def phase(self) -> str:
        """Current game phase: "betting" | "player" | "dealer" | "done"."""
        return self._phase

    # ------------------------------------------------------------------
    # Round start
    # ------------------------------------------------------------------

    def start_round(self, bet: int, deck: "Deck | None" = None) -> None:
        """Shuffle, deal initial cards, deduct bet from player bankroll.

        Args:
            bet:  Wager amount; must pass BettingSystem.validate_bet().
            deck: Optional pre-built Deck (useful for tests). A fresh
                  shuffled deck is created when omitted.

        Raises:
            ValueError: if bet is invalid.
        """
        BettingSystem.validate_bet(bet, self._player.bankroll)
        self._player.place_bet(bet)

        if deck is not None:
            self._deck = deck
        else:
            self._deck = Deck()
            self._deck.shuffle()

        player_hand = Hand(self._player.name)
        self._dealer_hand = Hand(self._dealer_name)
        for _ in range(2):
            player_hand.add_card(self._deck.deal(1)[0])
            self._dealer_hand.add_card(self._deck.deal(1)[0])

        self._hands = [player_hand]
        self._bets = [bet]
        self._current_hand_index = 0
        self._phase = "player"

        # Natural blackjack check — if player has 21 on 2 cards, skip to dealer
        if self._hands[0].blackjack_value() == 21:
            self._dealer_phase()

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def hit(self) -> None:
        """Draw one card to the current hand.

        Raises:
            RuntimeError: if not in player phase.
        """
        self._require_player_phase()
        self.current_hand.add_card(self._deck.deal(1)[0])
        if self.current_hand.blackjack_value() > 21:
            self._advance_hand()   # bust → move on

    def stand(self) -> None:
        """Stand on the current hand and move to the next (or dealer phase).

        Raises:
            RuntimeError: if not in player phase.
        """
        self._require_player_phase()
        self._advance_hand()

    def double_down(self) -> None:
        """Double the bet, draw exactly one card, then stand.

        Raises:
            RuntimeError: if not in player phase.
            ValueError:   if hand is not exactly 2 cards, or insufficient bankroll.
        """
        self._require_player_phase()
        hand = self.current_hand
        if hand.card_count() != 2:
            raise ValueError("Double down is only allowed on the first two cards.")
        extra = self._bets[self._current_hand_index]
        BettingSystem.validate_bet(extra, self._player.bankroll)
        self._player.place_bet(extra)
        self._bets[self._current_hand_index] *= 2
        hand.add_card(self._deck.deal(1)[0])
        self._advance_hand()   # forced stand after double

    def split(self) -> None:
        """Split a pair into two separate hands, each with the original bet.

        Raises:
            RuntimeError: if not in player phase.
            ValueError:   if hand is not a 2-card pair, or insufficient bankroll.
        """
        self._require_player_phase()
        hand = self.current_hand
        if hand.card_count() != 2:
            raise ValueError("Split is only allowed on the first two cards.")
        c0, c1 = hand.cards
        if c0.rank != c1.rank:
            raise ValueError("Split requires both cards to have the same rank.")

        extra = self._bets[self._current_hand_index]
        BettingSystem.validate_bet(extra, self._player.bankroll)
        self._player.place_bet(extra)

        h0 = Hand(self._player.name)
        h1 = Hand(self._player.name)
        h0.add_card(c0)
        h0.add_card(self._deck.deal(1)[0])
        h1.add_card(c1)
        h1.add_card(self._deck.deal(1)[0])

        self._hands[self._current_hand_index] = h0
        self._hands.insert(self._current_hand_index + 1, h1)
        self._bets.insert(self._current_hand_index + 1, extra)

    # ------------------------------------------------------------------
    # Results & settlement
    # ------------------------------------------------------------------

    def get_results(self) -> list[dict]:
        """Return one result dict per hand.

        Each dict contains:
            hand_index    – index into self.hands
            player_value  – final Blackjack value of the player hand
            dealer_value  – final Blackjack value of the dealer hand
            outcome       – "natural" | "win" | "push" | "bust" | "lose"
            payout        – amount to credit back to the player's bankroll
        """
        if self._phase != "done":
            raise RuntimeError("Round is not finished yet.")
        dealer_val = self._dealer_hand.blackjack_value()
        results = []
        for i, hand in enumerate(self._hands):
            player_val = hand.blackjack_value()
            bet = self._bets[i]

            if player_val > 21:
                outcome = "bust"
            elif dealer_val > 21:
                outcome = "win"
            elif player_val > dealer_val:
                # Natural: 2-card 21
                if hand.card_count() == 2 and player_val == 21:
                    outcome = "natural"
                else:
                    outcome = "win"
            elif player_val == dealer_val:
                outcome = "push"
            else:
                outcome = "lose"

            payout = BettingSystem.calculate_payout(bet, outcome, "blackjack")
            results.append({
                "hand_index":   i,
                "player_value": player_val,
                "dealer_value": dealer_val,
                "outcome":      outcome,
                "payout":       payout,
            })
        return results

    def settle_bets(self) -> None:
        """Credit payouts to the player's bankroll based on get_results()."""
        for result in self.get_results():
            self._player.win(result["payout"])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_player_phase(self) -> None:
        if self._phase != "player":
            raise RuntimeError(f"Cannot act in phase '{self._phase}'.")

    def _advance_hand(self) -> None:
        """Move to the next split hand, or enter the dealer phase."""
        self._current_hand_index += 1
        if self._current_hand_index >= len(self._hands):
            self._dealer_phase()

    def _dealer_phase(self) -> None:
        """Auto-play the dealer hand then mark the round done."""
        self._phase = "dealer"
        while AIDealer.should_hit(self._dealer_hand):
            self._dealer_hand.add_card(self._deck.deal(1)[0])
        self._phase = "done"

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"BlackjackGame(player={self._player.name!r}, "
            f"phase={self._phase!r}, "
            f"hands={len(self._hands)}, "
            f"dealer={self._dealer_hand.blackjack_value()})"
        )
