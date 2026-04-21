# Y2_2026_83758_casino_game

A multi-game casino suite built with Python and PyQt6, developed for Aalto University CS-A1123 Basics in Programming Y2 (Spring 2026).

## Games

### Deck Casino (Kasino Korttipeli)
Finnish card-taking game. Players capture table cards by playing a hand card whose **hand value** matches the sum of one or more table card groups. Three special cards carry bonus values:

| Card | Hand value | Table value | End-of-round point |
|------|-----------|------------|-------------------|
| Ace | 14 | 1 | +1 pt each |
| Diamond 10 | 16 | 10 | +2 pts |
| Spade 2 | 15 | 2 | +1 pt |

**Scoring** (first to 16 points wins):
- Each sweep (clearing the table): +1 pt
- Each Ace collected: +1 pt
- Most cards: +1 pt (no tie award)
- Most Spades: +2 pts (no tie award)
- Diamond 10 holder: +2 pts
- Spade 2 holder: +1 pt

Supports 2–4 players (human or AI). AI difficulty: Easy / Medium / Hard.

### Blackjack
Standard Blackjack against an AI dealer. Supports Hit, Stand, Double Down, and Split. Payouts: natural 2.5×, win 2×, push returns stake. Basic-strategy reference table is built into the AI dealer.

### Baccarat (Punto Banco)
Fully deterministic — no decisions after betting. Bet on Punto (1:1), Banco (1:1 minus 5% commission), or Tie (8:1). Third-card rules applied automatically.

## Installation

**Requires Python 3.10+ and PyQt6.**

```bash
pip install PyQt6
python main.py
```

No other dependencies are needed. All card art is drawn with QPainter — no image files required.

## Running Tests

```bash
python -m pytest tests/ -v          # 242 tests
python -m pytest tests/deck_casino_tests/ -v   # Deck Casino only
```

## Features

- **AI opponents** — three difficulty levels for Deck Casino; basic-strategy dealer for Blackjack
- **Save / Load** — full mid-round game state persisted to JSON; save file keyed by player roster so multiple groups can have separate saves
- **Bankroll persistence** — bankroll carries across Blackjack and Baccarat sessions (`bankrolls.json`)
- **Move history** — every action recorded with an auto-generated improvement tip; reviewable in the History panel
- **Hint mode** — toggle hand-value badges on cards during Deck Casino
- **Tutorial overlay** — step-by-step in-game guide for new players
- **Card animations** — deal fade-in and flip animations via QTimer

## Project Structure

```
main.py                  # entry point
model/                   # pure game logic (no PyQt6)
  card.py                # dual hand/table value design
  deck.py                # 52-card draw pile
  hand.py                # card aggregator
  player.py              # participant state across all games
  casino_take_algorithm.py  # subset-sum validator (recursive backtracking)
  deck_casino_game.py    # Deck Casino game loop
  blackjack_game.py      # Blackjack + AIDealer
  baccarat_game.py       # Punto Banco Baccarat
  ai_opponent.py         # 3-difficulty AI for Deck Casino
  betting_system.py      # payout calculator
  file_manager.py        # JSON save/load + move history
controller/
  game_manager.py        # thin game registry
view/                    # PyQt6 GUI (no game logic)
  main_window.py         # application shell + signal wiring
  lobby_view.py          # game selection screen
  deck_casino_view.py    # Deck Casino table
  blackjack_view.py      # Blackjack betting/play interface
  baccarat_view.py       # Punto vs Banco layout
  card_widget.py         # QPainter card rendering
  drawn_assets.py        # shared overlays, chip widget, avatar
  game_history_view.py   # move history panel
tests/                   # 242 unit tests (pytest)
```

## UML Diagrams

[Open diagram in mxGraph editor](https://gitmanager.cs.aalto.fi/static/CS-A1121_2026Autumn/_static/mxgraph_mini/javascript/examples/grapheditor/www/index.html)

## Authors

Developed by Jatlyson Ang for Aalto University CS-A1123 Basics in Programming Y2, Spring 2026.
