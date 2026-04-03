from model.card import Card
from model.deck import Deck
from model.hand import Hand
from model.player import Player
from model.betting_system import BettingSystem


def _baccarat_card_value(card: Card) -> int:
    """Return the Baccarat point value of a single card.

    Ace = 1, 2-9 = face value, 10/J/Q/K = 0.
    """
    if card.rank in ("J", "Q", "K", "10"):
        return 0
    if card.rank == "A":
        return 1
    return int(card.rank)


def _baccarat_hand_total(hand: Hand) -> int:
    """Return the Baccarat total (sum of card values mod 10)."""
    return sum(_baccarat_card_value(c) for c in hand.cards) % 10


class BaccaratGame:
    """One round of Punto Banco Baccarat.

    Flow
    ────
    1. start_round(bet, bet_type) — deal 2 cards to Punto and Banco.
    2. draw_third_card()          — apply the standard third-card rules.
    3. get_result()               — determine winner and payout.
    4. settle_bet()               — credit payout to player bankroll.

    Bet types: "punto" | "banco" | "tie"

    Natural: Punto or Banco total is 8 or 9 on the first two cards.
    A natural ends the round immediately (no third card drawn).

    Third-card rules (deterministic)
    ─────────────────────────────────
    Punto draws if total 0–5; stands on 6 or 7.
    Banco draws according to the standard rule table keyed on Banco's
    current total and (if Punto drew) Punto's third card value.
    """

    def __init__(self, player: Player) -> None:
        self._player = player
        self._deck: Deck = Deck()
        self._punto_hand: Hand = Hand("Punto")
        self._banco_hand: Hand = Hand("Banco")
        self._bet: int = 0
        self._bet_type: str = "punto"
        self._natural: bool = False
        self._phase: str = "betting"   # "betting" | "drawing" | "done"

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def punto_hand(self) -> Hand:
        return self._punto_hand

    @property
    def banco_hand(self) -> Hand:
        return self._banco_hand

    @property
    def natural(self) -> bool:
        return self._natural

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def player(self) -> Player:
        return self._player

    # ------------------------------------------------------------------
    # Convenience totals
    # ------------------------------------------------------------------

    def punto_total(self) -> int:
        return _baccarat_hand_total(self._punto_hand)

    def banco_total(self) -> int:
        return _baccarat_hand_total(self._banco_hand)

    # ------------------------------------------------------------------
    # Round start
    # ------------------------------------------------------------------

    def start_round(self, bet: int, bet_type: str = "punto",
                    deck: "Deck | None" = None) -> None:
        """Deal initial two cards to Punto and Banco and deduct the bet.

        Args:
            bet:      Wager amount.
            bet_type: "punto" | "banco" | "tie"
            deck:     Optional pre-built Deck (useful for tests). A fresh
                      shuffled deck is created when omitted.

        Raises:
            ValueError: if bet is invalid or bet_type is unknown.
        """
        if bet_type not in ("punto", "banco", "tie"):
            raise ValueError(f"Unknown bet_type: '{bet_type}'.")
        BettingSystem.validate_bet(bet, self._player.bankroll)
        self._player.place_bet(bet)

        self._bet = bet
        self._bet_type = bet_type
        self._natural = False

        if deck is not None:
            self._deck = deck
        else:
            self._deck = Deck()
            self._deck.shuffle()

        self._punto_hand = Hand("Punto")
        self._banco_hand = Hand("Banco")

        # Deal: Punto, Banco, Punto, Banco
        for _ in range(2):
            self._punto_hand.add_card(self._deck.deal(1)[0])
            self._banco_hand.add_card(self._deck.deal(1)[0])

        # Natural check
        if self.punto_total() >= 8 or self.banco_total() >= 8:
            self._natural = True
            self._phase = "done"
        else:
            self._phase = "drawing"

    # ------------------------------------------------------------------
    # Third-card drawing
    # ------------------------------------------------------------------

    def draw_third_card(self) -> None:
        """Apply the standard Punto Banco third-card rules.

        Must be called exactly once while phase == "drawing".
        Sets phase to "done" on completion.

        Raises:
            RuntimeError: if not in drawing phase (e.g., after a natural).
        """
        if self._phase != "drawing":
            raise RuntimeError(
                f"draw_third_card() called in phase '{self._phase}'."
            )

        punto_total = self.punto_total()
        banco_total = self.banco_total()
        punto_drew = False
        punto_third_value: int | None = None

        # ── Punto third-card rule ─────────────────────────────────────
        if punto_total <= 5:
            card = self._deck.deal(1)[0]
            self._punto_hand.add_card(card)
            punto_drew = True
            punto_third_value = _baccarat_card_value(card)

        # ── Banco third-card rule ─────────────────────────────────────
        if not punto_drew:
            # Punto stood → Banco draws on 0-5
            if banco_total <= 5:
                self._banco_hand.add_card(self._deck.deal(1)[0])
        else:
            # Punto drew → deterministic table
            if self._banco_draws(banco_total, punto_third_value):
                self._banco_hand.add_card(self._deck.deal(1)[0])

        self._phase = "done"

    # ------------------------------------------------------------------
    # Result & settlement
    # ------------------------------------------------------------------

    def get_result(self) -> dict:
        """Return the round result.

        Returns a dict with:
            punto_total  – final Punto total
            banco_total  – final Banco total
            outcome      – "punto_win" | "banco_win" | "tie"
            natural      – True if the round ended on a natural
            payout       – amount to credit to the player's bankroll
        """
        if self._phase != "done":
            raise RuntimeError("Round is not finished yet.")

        pt = self.punto_total()
        bt = self.banco_total()

        if pt > bt:
            outcome = "punto_win"
        elif bt > pt:
            outcome = "banco_win"
        else:
            outcome = "tie"

        payout = BettingSystem.calculate_payout(
            self._bet, outcome, "baccarat", self._bet_type
        )
        return {
            "punto_total": pt,
            "banco_total": bt,
            "outcome":     outcome,
            "natural":     self._natural,
            "payout":      payout,
        }

    def settle_bet(self) -> None:
        """Credit the payout to the player's bankroll."""
        result = self.get_result()
        self._player.win(result["payout"])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _banco_draws(banco_total: int, punto_third: int | None) -> bool:
        """Return True if Banco must draw according to the standard rule table.

        Args:
            banco_total:  Banco's current 2-card total.
            punto_third:  Punto's third card value (0-9), or None if Punto stood.
        """
        if punto_third is None:
            return banco_total <= 5

        if banco_total <= 2:
            return True
        if banco_total == 3:
            return punto_third != 8
        if banco_total == 4:
            return punto_third in (2, 3, 4, 5, 6, 7)
        if banco_total == 5:
            return punto_third in (4, 5, 6, 7)
        if banco_total == 6:
            return punto_third in (6, 7)
        # banco_total == 7: always stand
        return False

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"BaccaratGame(player={self._player.name!r}, "
            f"phase={self._phase!r}, "
            f"punto={self.punto_total()}, banco={self.banco_total()})"
        )
