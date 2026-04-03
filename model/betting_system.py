class BettingSystem:
    """Validates bets and calculates payouts for Blackjack and Baccarat.

    Payout structure
    ────────────────
    Blackjack:
        natural (Ace + 10-value on first 2 cards)  →  2.5x bet
        win                                         →  2x bet
        push (tie)                                  →  1x bet (returned)
        bust / lose                                 →  0

    Baccarat (bet_type = "punto" | "banco" | "tie"):
        Punto win   →  2x bet (1:1)
        Banco win   →  int(1.95 * bet) (1:1 minus 5% commission)
        Tie         →  9x bet (8:1 + stake returned)
        Push        →  1x bet (e.g. Punto/Banco bet when result is Tie)
        Lose        →  0
    """

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_bet(bet: int, bankroll: int) -> None:
        """Raise ValueError if the bet is invalid.

        Args:
            bet: Proposed bet amount.
            bankroll: Player's current bankroll.

        Raises:
            ValueError: if bet <= 0 or bet > bankroll.
        """
        if bet <= 0:
            raise ValueError("Bet must be greater than 0.")
        if bet > bankroll:
            raise ValueError(f"Bet {bet} exceeds bankroll {bankroll}.")

    # ------------------------------------------------------------------
    # Payout calculation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_payout(bet: int, outcome: str, game_type: str,
                         bet_type: str | None = None) -> int:
        """Return the total payout (amount added back to bankroll).

        For a win the payout covers the original stake plus profit.
        For a push the original stake is returned.
        For a loss the payout is 0 (stake already deducted by place_bet).

        Args:
            bet:       The original bet amount.
            outcome:   "natural" | "win" | "push" | "bust" | "lose"
                       or for Baccarat: "punto_win" | "banco_win" | "tie"
            game_type: "blackjack" | "baccarat"
            bet_type:  Baccarat only — "punto" | "banco" | "tie"

        Returns:
            Integer payout to credit to the player's bankroll.
        """
        if game_type == "blackjack":
            return BettingSystem._blackjack_payout(bet, outcome)
        if game_type == "baccarat":
            return BettingSystem._baccarat_payout(bet, outcome, bet_type or "punto")
        raise ValueError(f"Unknown game_type: '{game_type}'")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _blackjack_payout(bet: int, outcome: str) -> int:
        if outcome == "natural":
            return int(bet * 2.5)   # 1.5 : 1
        if outcome == "win":
            return bet * 2          # 1 : 1
        if outcome == "push":
            return bet              # stake returned
        return 0                    # bust / lose

    @staticmethod
    def _baccarat_payout(bet: int, outcome: str, bet_type: str) -> int:
        """Resolve a Baccarat bet.

        outcome:  "punto_win" | "banco_win" | "tie"
        bet_type: "punto"     | "banco"     | "tie"
        """
        if outcome == "tie":
            if bet_type == "tie":
                return bet * 9      # 8 : 1
            return bet              # push — Punto/Banco bets are returned

        if outcome == "punto_win":
            if bet_type == "punto":
                return bet * 2      # 1 : 1
            return 0                # banco/tie bet loses

        if outcome == "banco_win":
            if bet_type == "banco":
                return int(bet * 1.95)   # 1 : 1 minus 5% commission
            return 0                     # punto/tie bet loses

        raise ValueError(f"Unknown baccarat outcome: '{outcome}'")
