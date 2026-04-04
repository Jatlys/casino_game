# Deck Casino — Codebase Explained

## Table of Contents
1. [Game Rules](#1-game-rules)
2. [Architecture Overview](#2-architecture-overview)
3. [Model Layer](#3-model-layer)
   - [Card](#31-card)
   - [Deck](#32-deck)
   - [Hand](#33-hand)
   - [Player](#34-player)
   - [BettingSystem](#35-bettingsystem)
   - [CasinoTakeAlgorithm](#36-casinotakealgorithm)
   - [DeckCasinoGame](#37-deckcasinogame)
   - [AIOpponent](#38-aiopponent)
   - [BlackjackGame](#39-blackjackgame)
   - [BaccaratGame](#310-baccaratgame)
   - [FileManager](#311-filemanager)
4. [Controller Layer](#4-controller-layer)
5. [View Layer](#5-view-layer)
   - [CardWidget](#51-cardwidget)
   - [DeckCasinoView](#52-deckcasinoview)
   - [MainWindow](#53-mainwindow)
   - [LobbyView](#54-lobbyview)
   - [BlackjackView](#55-blackjackview)
   - [BaccaratView](#56-baccaratview)
   - [DeckCasinoInstructionsDialog](#57-deckcasinoinstructionsdialog)
   - [DrawnAssets](#58-drawnassets)
   - [PlayerBadgeWidget](#59-playerbadgewidget)
6. [Entry Point](#6-entry-point)
7. [Data Flow: A Complete Turn](#7-data-flow-a-complete-turn)

---

## 1. Game Rules

Deck Casino is a Finnish card-taking game (Kasino). Here is how it works:

### Goal
The first player to reach **16 points** across multiple rounds wins.

### Setup (per round)
- A standard 52-card deck is shuffled.
- **4 cards** are dealt face-up to the table.
- **4 cards** are dealt to each player's hand (hidden from others).
- The remaining cards form the **stock pile** (face-down draw pile).

### On Each Turn
A player picks one card from their hand and does one of two things:

**Take Cards** — Select one or more table cards whose values add up to the played card's **hand value**, then press "Take Cards". All selected table cards plus the played card go into the player's collection.

**Place Card** — Put the selected hand card face-up on the table. Required when no valid take exists.

After the action, the player draws one card from the stock (if available), and it is the next player's turn.

### Taking Multiple Groups at Once
If the played card's hand value matches multiple **non-overlapping** groups of table cards simultaneously, all groups can be taken in a single move.

Example: You play J (value 11). The table has J (=11), 6+5 (=11), and 10+A (=11). All three groups are non-overlapping, so you take all five table cards at once.

### Sweep
If taking cards **clears the entire table**, the player scores a **Sweep** (worth 1 point at round end). The table is empty and the next player must place a card.

### End of Round
The round ends when the stock is empty and all hands are empty. The last player who took cards collects any cards still on the table. Points are tallied and added to cumulative scores.

### Special Cards (Dual Values)
Three cards have a **higher hand value** (used when playing from hand) than their **table value** (used when sitting on the table):

| Card        | Hand Value | Table Value | Bonus at Round End |
|-------------|-----------|-------------|---------------------|
| Diamond-10  | 16        | 10          | 2 pts               |
| Spade-2     | 15        | 2           | 1 pt                |
| Any Ace (x4)| 14        | 1           | 1 pt each           |

All other cards have the same value in hand and on the table (2-10, J=11, Q=12, K=13).

### Scoring (per round)
| Condition                    | Points      |
|------------------------------|-------------|
| Each Sweep scored this round | 1 pt each   |
| Each Ace in your collection  | 1 pt each   |
| Most cards collected         | 1 pt (no tie)|
| Most Spades collected        | 2 pts (no tie)|
| Diamond-10 in collection     | 2 pts       |
| Spade-2 in collection        | 1 pt        |

---

## 2. Architecture Overview

The project follows the **MVC (Model-View-Controller)** pattern:

```
main.py
  └── view/main_window.py          (Controller-View bridge; wires everything)
        ├── controller/game_manager.py   (Controller: launches and holds active game)
        ├── model/
        │     ├── card.py               (Data: a single card, dual-value design)
        │     ├── deck.py               (Data: 52-card draw pile)
        │     ├── hand.py               (Data: a player's held cards, incl. Blackjack value)
        │     ├── player.py             (Data: player state — hand, collection, score, bankroll)
        │     ├── betting_system.py     (Logic: bet validation + payout calc for BJ/Baccarat)
        │     ├── casino_take_algorithm.py  (Logic: validates and finds valid takes)
        │     ├── deck_casino_game.py   (Logic: full Deck Casino game loop and scoring)
        │     ├── blackjack_game.py     (Logic: Blackjack round — hit/stand/double/split + AIDealer)
        │     ├── baccarat_game.py      (Logic: Punto Banco Baccarat round + third-card rules)
        │     ├── ai_opponent.py        (Logic: Deck Casino AI, 3 difficulty levels)
        │     └── file_manager.py       (Persistence: save/load JSON, move history)
        └── view/
              ├── lobby_view.py             (UI: game selection screen — all 3 games wired)
              ├── deck_casino_view.py       (UI: Deck Casino table, hand, action buttons)
              ├── blackjack_view.py         (UI: Blackjack table with betting panel)
              ├── baccarat_view.py          (UI: Baccarat Punto vs Banco layout)
              ├── card_widget.py            (UI: renders a single card with QPainter)
              ├── player_badge_widget.py    (UI: score badge per player in the score row)
              ├── drawn_assets.py           (UI: shared QPainter assets and overlay widgets)
              ├── deck_casino_tutorial.py   (UI: step-by-step tutorial overlay)
              └── game_instructions/
                    └── deck_casino.py      (UI: tabbed How-to-Play dialog)
```

**Key design principle:** The model knows nothing about the UI. The view knows nothing about game logic. `MainWindow` connects them by listening to view signals and calling model methods.

---

## 3. Model Layer

### 3.1 `Card`
**File:** [model/card.py](model/card.py)

Represents a single immutable playing card. The central design decision is the **dual-value system**.

```
Card(suit, rank)
```

**`hand_value()`** — value used when this card is **played from the hand** (the target sum for takes):
- Ace → 14
- Diamond-10 → 16
- Spade-2 → 15
- J/Q/K → 11/12/13
- All others → face value (int)

**`table_value()`** — value used when this card **sits on the table** (used in subset-sum checks):
- Ace → 1
- All others (including Diamond-10 and Spade-2) → face value

**`is_special()`** — returns `True` for Ace, Diamond-10, Spade-2. Used by the view to draw a gold border.

`Card` implements `__eq__` and `__hash__` based on `(suit, rank)`, so cards can safely be stored in sets and used as frozenset members.

---

### 3.2 `Deck`
**File:** [model/deck.py](model/deck.py)

Creates all 52 unique `Card` objects (4 suits x 13 ranks) on construction. Internally a list where **the end of the list is the "top"** of the deck.

**`shuffle()`** — shuffles the internal list in place using `random.shuffle`.

**`deal(n)`** — pops `n` cards from the end of the list and returns them. Raises `ValueError` if fewer than `n` cards remain.

**`is_empty()`** — returns `True` when no cards remain.

**`__len__()`** — returns the current number of remaining cards (used by the view to display the stock count).

---

### 3.3 `Hand`
**File:** [model/hand.py](model/hand.py)

A simple ordered list of `Card` objects belonging to one participant. Used by all three games.

**`add_card(card)`** — appends a card.

**`remove_card(card)`** — removes a specific card; raises `ValueError` if it is not present.

**`card_count()`** — returns the number of cards currently in the hand.

**`is_empty()`** — returns `True` when no cards remain.

**`get_value()`** — sums `hand_value()` for every card (Deck Casino; informational only).

**`blackjack_value()`** — returns the Blackjack total. Aces count as 11 and are demoted to 1 as needed to avoid bust. Face cards (J, Q, K) count as 10. Used by `BlackjackGame` and `AIDealer`.

---

### 3.4 `Player`
**File:** [model/player.py](model/player.py)

Tracks everything about a single participant across rounds. Supports both human and AI players, and is shared across all three games.

```python
Player(name, is_ai=False, difficulty="hard", bankroll=1000)
```

**State:**
- `hand` — a `Hand` instance (the cards currently held)
- `_collection` — list of `Card` objects taken this round (Deck Casino only)
- `_sweeps` — number of sweeps scored this round (Deck Casino only)
- `_total_score` — cumulative score across all rounds (Deck Casino only)
- `_bankroll` — chip count for Blackjack and Baccarat (starts at $1000 by default)
- `_is_ai` — `True` if this player is controlled by `AIOpponent`
- `_difficulty` — `"easy"`, `"medium"`, or `"hard"` (AI only; ignored for humans)

**Deck Casino methods:**

**`add_to_collection(cards)`** — adds one card or a list of cards to the collection.

**`add_sweep()`** — increments the sweep counter.

**`add_score(points)`** — adds points to the cumulative total.

**`reset_for_round()`** — clears the hand, collection, and sweeps. Does **not** reset `total_score` or `bankroll`.

**Bankroll methods (Blackjack / Baccarat):**

**`place_bet(amount)`** — deducts the bet from `_bankroll`. Raises `ValueError` if `amount <= 0` or exceeds the bankroll.

**`win(payout)`** — credits a payout (returned stake + winnings) to `_bankroll`.

**`lose()`** — no-op; bankroll was already reduced by `place_bet()`.

---

### 3.5 `BettingSystem`
**File:** [model/betting_system.py](model/betting_system.py)

Validates bets and calculates payouts for Blackjack and Baccarat. All methods are `@staticmethod` — no state.

#### `validate_bet(bet, bankroll)`
Raises `ValueError` if `bet <= 0` or `bet > bankroll`. Called before deducting the stake.

#### `calculate_payout(bet, outcome, game_type, bet_type=None) → int`
Returns the total integer amount to credit back to the bankroll (includes the returned stake on a win or push).

**Blackjack payouts (`game_type="blackjack"`):**

| Outcome   | Payout             |
|-----------|--------------------|
| `natural` | `int(bet * 2.5)` (1.5:1) |
| `win`     | `bet * 2` (1:1)    |
| `push`    | `bet` (stake returned) |
| `bust` / `lose` | `0`         |

**Baccarat payouts (`game_type="baccarat"`, requires `bet_type`):**

| Outcome      | `bet_type` | Payout                   |
|--------------|------------|--------------------------|
| `tie`        | `"tie"`    | `bet * 9` (8:1)          |
| `tie`        | anything else | `bet` (push — stake returned) |
| `punto_win`  | `"punto"`  | `bet * 2` (1:1)          |
| `punto_win`  | other      | `0`                      |
| `banco_win`  | `"banco"`  | `int(bet * 1.95)` (5% commission) |
| `banco_win`  | other      | `0`                      |

---

### 3.6 `CasinoTakeAlgorithm`
**File:** [model/casino_take_algorithm.py](model/casino_take_algorithm.py)

The core game logic for validating and discovering takes. All methods are `@staticmethod` — this class has no state.

#### `get_valid_takes(played_card, table_cards)`
Finds every non-empty subset of `table_cards` whose `table_value()` sum equals `played_card.hand_value()`. Uses `itertools.combinations` to iterate over all subsets of size 1 through `len(table_cards)`. Returns a list of `frozenset` objects.

```python
target = played_card.hand_value()
for r in range(1, len(table_cards) + 1):
    for combo in itertools.combinations(table_cards, r):
        if sum(c.table_value() for c in combo) == target:
            valid.append(frozenset(combo))
```

This is a brute-force subset-sum search — acceptable because there are at most ~8-12 table cards in practice.

#### `is_valid_take(played_card, chosen_cards, table_cards)`
Validates that the player's chosen set of cards is a legal take. A chosen set is valid if:
1. It is non-empty.
2. It is a subset of the actual table cards.
3. It can be **partitioned** into one or more non-overlapping valid subsets (each summing to `hand_value()`).

Step 3 delegates to `_can_cover`.

#### `_can_cover(remaining, valid_subsets)`
A **recursive backtracking** algorithm. It checks if `remaining` (the set of chosen cards) can be completely covered by selecting non-overlapping subsets from `valid_subsets`.

```
Base case:  remaining is empty → True (all cards accounted for)
Recursive:  for each valid subset that fits inside remaining,
              recurse with (remaining - subset)
            if any path returns True → True
            otherwise → False
```

This correctly handles the multi-group take rule (e.g., playing J=11 and taking three separate groups that each sum to 11).

---

### 3.7 `DeckCasinoGame`
**File:** [model/deck_casino_game.py](model/deck_casino_game.py)

The **game loop**. Owns the deck, table cards, player list, and turn tracking.

**`start_game()`** — resets and runs setup:
1. Creates a fresh `Deck` and shuffles it.
2. Deals 4 cards to the table.
3. Calls `player.reset_for_round()` for each player, then deals 4 cards to each hand.
4. Resets `_last_taker` and `_turn_index`.

**`play_card(card, take)`** — executes the current player's turn:
1. Verifies `card` is in the current player's hand; removes it.
2. **If `take` is not None (taking):**
   - Calls `CasinoTakeAlgorithm.is_valid_take()` — raises `ValueError` if invalid.
   - Removes taken cards from `_table_cards`.
   - Adds `[card] + list(take)` to the player's collection.
   - Records the current player as `_last_taker`.
   - Calls `check_sweep()`.
3. **If `take` is None (placing):**
   - Appends the card to `_table_cards`.
4. Draws one card from stock into the player's hand (if stock is not empty).
5. Calls `advance_turn()`.

**`check_sweep()`** — if `_table_cards` is empty, calls `current_player.add_sweep()`.

**`advance_turn()`** — increments `_turn_index` modulo the number of players (wraps around).

**`is_round_over()`** — returns `True` when the stock is empty and every player's hand is empty.

**`end_round()`** — finalises the round:
1. Gives any remaining table cards to `_last_taker`.
2. Calls `calculate_scores()`.

**`calculate_scores()`** — awards points to each player in this order:
1. Sweeps: `player.sweeps` points per player.
2. Aces: 1 point per Ace in each player's collection.
3. Most cards: 1 point to the player with the most collected cards (no award on a tie).
4. Most Spades: 2 points to the player with the most Spades (no award on a tie).
5. Diamond-10 holder: 2 points.
6. Spade-2 holder: 1 point.

**`has_winner()`** — returns `True` if any player's `total_score >= 16`.

---

### 3.8 `AIOpponent`
**File:** [model/ai_opponent.py](model/ai_opponent.py)

Stateless AI decision-maker for Deck Casino. All methods are `@staticmethod`. Called by `MainWindow._after_deck_casino_action()` for every AI player's turn.

```python
AIOpponent.decide_action(game, difficulty) → (Card, frozenset | None)
```

Returns `(card_to_play, take)` where `take=None` means place the card.

#### Three difficulty levels

**Easy** (`_decide_easy`) — picks any random valid take, or places a random card. No strategy.

**Medium** (`_decide_medium`) — applies three priorities:
1. Sweep the table if possible.
2. Maximise the number of cards taken.
3. Place the card with the lowest hand value.

**Hard** (`_decide_hard`) — full six-priority strategy:
1. **Sweep** — take all table cards if possible (using the least-valuable hand card).
2. **Prize capture** — take Diamond-10 or Spade-2 from the table.
3. **Maximise count** — take the largest group of cards.
4. **Special preference** — among equal-count options, prefer groups containing special cards.
5. **Sweep-safe placement** — if no take is available, place a card that does not let any opponent sweep the table on their next turn.
6. **Lowest placement** — fall back to placing the card with the lowest hand value.

#### Placement safety helpers

**`_choose_placement(hand_cards, table)`** — sorts candidates by hand value; returns the first one that does not enable a sweep, or the lowest-value card if all would enable one.

**`_placement_enables_sweep(card, table)`** — returns `True` if adding `card` to the table would allow any hand value (2–16) to sweep the whole table.

**`_sweepable_by_value(hand_value, table)`** — checks whether a single card with `hand_value` could legally take every card currently on the table, using `_can_cover`.

---

### 3.9 `BlackjackGame`
**File:** [model/blackjack_game.py](model/blackjack_game.py)

One round of Blackjack: a single human `Player` vs. the `AIDealer`. Supports split hands.

#### Phases

| Phase      | Meaning                                                   |
|------------|-----------------------------------------------------------|
| `"betting"` | Waiting for `start_round(bet)` call                      |
| `"player"` | Player acts (hit / stand / double_down / split)           |
| `"dealer"` | Dealer auto-plays after all player hands are settled      |
| `"done"`   | Round over; call `get_results()` then `settle_bets()`     |

#### Split support
- `_hands` — list of `Hand` objects (length > 1 after a split).
- `_bets` — mirrors `_hands` with the bet amount for each hand.
- `_current_hand_index` — points to the hand currently being played.

#### Key methods

**`start_round(bet, deck=None)`** — validates and deducts the bet via `BettingSystem`, shuffles a fresh deck, deals 2 cards each to the player and dealer. If the player has a natural 21, jumps straight to the dealer phase.

**`hit()`** — draws one card to the current hand; advances past it automatically on bust.

**`stand()`** — stands on the current hand and moves to the next (or dealer phase).

**`double_down()`** — doubles the bet, draws exactly one card, then stands. Only allowed on the first two cards if the player has sufficient bankroll.

**`split()`** — splits a 2-card same-rank hand into two hands, each with the original bet. Each new hand gets one additional card from the deck. Requires sufficient bankroll.

**`get_results() → list[dict]`** — returns one result dict per hand with keys `hand_index`, `player_value`, `dealer_value`, `outcome` (`"natural"` | `"win"` | `"push"` | `"bust"` | `"lose"`), and `payout`.

**`settle_bets()`** — credits each hand's payout to `player.bankroll` via `player.win()`.

#### `AIDealer`
Inner class (same file). Dealer hits on any total < 17 and stands on 17+.

**`should_hit(hand)`** — returns `True` if `hand.blackjack_value() < 17`.

**`basic_strategy_action(player_total, dealer_upcard)`** — returns the canonical basic-strategy recommendation (`"hit"` | `"stand"` | `"double"`) for a given hard total vs. dealer upcard. The strategy table is built lazily on first call via `_build_strategy()`.

---

### 3.10 `BaccaratGame`
**File:** [model/baccarat_game.py](model/baccarat_game.py)

One round of Punto Banco Baccarat. Fully deterministic once cards are dealt — no player decisions after betting.

#### Flow

1. `start_round(bet, bet_type, deck=None)` — validates and deducts the bet, deals 2 cards each to Punto and Banco. Sets `natural=True` and phase to `"done"` immediately if either side totals 8 or 9.
2. `draw_third_card()` — applies the standard third-card rule table (only callable in phase `"drawing"`).
3. `get_result()` — determines winner and payout; returns a dict.
4. `settle_bet()` — credits the payout to `player.bankroll`.

#### Bet types
`"punto"` | `"banco"` | `"tie"`

#### Card values
- Ace = 1, 2–9 = face value, 10/J/Q/K = 0. Hand total = sum mod 10.

#### Third-card rules
- **Punto** draws if total 0–5; stands on 6 or 7.
- **Banco** draws according to the standard rule table (`_banco_draws`) keyed on Banco's current total and Punto's third card value (if Punto drew).

**`get_result() → dict`** — keys: `punto_total`, `banco_total`, `outcome` (`"punto_win"` | `"banco_win"` | `"tie"`), `natural`, `payout`.

---

### 3.11 `FileManager`
**File:** [model/file_manager.py](model/file_manager.py)

Handles JSON serialization of the full Deck Casino game state and per-move history. All methods are `@staticmethod`. Save files are named `save_{player1}_{player2}_....json` in the working directory (keyed by the player roster so each lineup has its own file).

#### Save format
```json
{
  "turn_index": 0,
  "table_cards": [{"suit": "...", "rank": "..."}, ...],
  "stock":       [{"suit": "...", "rank": "..."}, ...],
  "players": [
    {
      "name": "...", "is_ai": false, "difficulty": "hard",
      "total_score": 0, "sweeps": 0,
      "hand":       [...],
      "collection": [...]
    }
  ],
  "move_history": [
    {"player": "...", "played": "...", "action": "take|place",
     "took": [...], "advice": "..."}
  ]
}
```

**`save(game, move_history, player_names=None)`** — serializes the current `DeckCasinoGame` instance plus the move history list to a roster-keyed JSON file. Called after every action by `MainWindow`.

**`load(player_names=None)`** — reads the matching save file if it exists and returns `(game, move_history)`, or `None` if no file is found.

**`restore(data)`** — reconstructs a `DeckCasinoGame` from a parsed JSON dict. Uses `object.__new__` to bypass `__init__` so no fresh game is started — all state is injected directly.

**`record_move(player_name, played_card, take, table_before)`** — builds a move record dict including an automatically generated improvement tip:
- If placing when a take was available → suggests taking.
- If a sweep was missed → flags it.
- If special cards were captured → acknowledges it.
- Otherwise → "Solid take."

---

## 4. Controller Layer

### `GameManager`
**File:** [controller/game_manager.py](controller/game_manager.py)

A thin registry that holds the active game instance and player roster.

**`set_players(players)`** — registers the player list.

**`start_deck_casino(players)`** — instantiates `DeckCasinoGame`, calls `start_game()`, and stores the result in `_active_game`. The `MainWindow` then reads `active_game` to refresh the view.

`GameManager` is designed to support multiple game types (Blackjack, Baccarat), which is why it uses a generic `_active_game` attribute rather than a game-specific one. Blackjack and Baccarat games are launched directly by `MainWindow` without going through `GameManager`.

---

## 5. View Layer

All views use **PyQt6**. No external image files are used — all card and UI art is drawn with `QPainter`.

### 5.1 `CardWidget`
**File:** [view/card_widget.py](view/card_widget.py)

Renders a single card as a 70x98 pixel widget (standard 1:1.4 poker card ratio).

**Three rendering modes** (controlled by `_card` and `_face_down`):
- `card=None, face_down=False` → dashed placeholder slot
- `face_down=True` → blue card back with white inner border
- `card set, face_down=False` → card face

**`_draw_face()`** draws:
1. White rounded rectangle background.
2. Rank and suit symbol in the top-left (small font).
3. Large suit symbol centred.
4. Rank and suit in the bottom-right (rotated 180°).
5. A **gold border** if `card.is_special()` is `True`.
6. A **hint badge** (top-right, shows `hand_value()`) when hint mode is active.

**`set_selected(bool)`** — triggers a repaint; a blue border is drawn over the card when selected.

**`set_hint_mode(bool)`** — class-level flag, so toggling hint mode affects all `CardWidget` instances simultaneously.

**`clicked` signal** — emitted on `mousePressEvent`; wired up by the parent view.

---

### 5.2 `DeckCasinoView`
**File:** [view/deck_casino_view.py](view/deck_casino_view.py)

The main Deck Casino game table UI. Manages card selection state and emits signals to `MainWindow` when the player acts.

**Layout (top to bottom):**
- Title bar with current player's name
- Score row — one `PlayerBadgeWidget` per player + stock count label
- `TableZoneWidget` — green felt area containing table `CardWidget`s
- Hand zone — current player's hand cards
- Tutorial overlay (hidden by default)
- Action button row: Lobby | How to Play | Hint Mode | Place Card | Take Cards

**Selection state:**
- `_selected_hand_card` — the one hand card currently selected (at most one at a time)
- `_selected_table_cards` — a `set` of table cards currently selected (can be multiple)

**`refresh(game)`** — called after every action; rebuilds the entire view from the current game state (no partial updates). Clears all selections.

**`show_sweep_flash(player_name, hint_text)`** — delegates to `SweepFlashOverlay.flash()`. Called by `MainWindow` when a sweep is detected.

**`show_point_toast(title, subtitle, accent)`** — delegates to `PointToastOverlay.show_event()`. Called by `MainWindow` when a notable card (Ace, Diamond-10, Spade-2) is captured.

**`is_hint_mode`** — property; `True` when the Hint Mode button is toggled on.

**Interaction flow:**
1. `_on_hand_card_clicked()` — sets `_selected_hand_card`; clears table selection.
2. `_on_table_card_clicked()` — toggles a table card in/out of `_selected_table_cards` (only if a hand card is already selected).
3. `_update_buttons()` — enables/disables "Take Cards" and "Place Card" based on selection state.
4. `_on_take_clicked()` — emits `take_requested(hand_card, frozenset(table_cards))`.
5. `_on_place_clicked()` — emits `place_requested(hand_card)`.

These signals are received by `MainWindow`, which calls the model and then calls `refresh()` again.

**`TableZoneWidget`** is a small helper widget (also imported by `BlackjackView` and `BaccaratView`) that paints a dark-green rounded rectangle for the felt background.

---

### 5.3 `MainWindow`
**File:** [view/main_window.py](view/main_window.py)

The application shell and the primary **wiring point** between view signals and model methods. It is a `QMainWindow` with:
- A persistent `SidebarWidget` on the left (player name, score, nav buttons).
- A `QStackedWidget` on the right that swaps between Lobby and game views.
- A `_move_history` list that accumulates `FileManager.record_move()` dicts throughout the Deck Casino session.

Four views are registered at startup: `LobbyView`, `DeckCasinoView`, `BlackjackView`, `BaccaratView`.

**Game launch flow (`_launch_deck_casino`):**
1. Calls `FileManager.load(player_names)` — if a matching save exists, prompts the user to resume. If accepted, restores the game directly and skips setup.
2. Shows `PlayerSetupDialog` — two-mode dialog:
   - **Player vs Player**: choose 2–4 players, enter names.
   - **Player vs Computer**: enter your name, choose AI difficulty (Easy / Medium / Hard).
3. Shows `TutorialModeDialog` — asks if the player wants a tutorial.
4. Creates `Player` objects (with `is_ai=True` for the computer player), calls `game_manager.start_deck_casino(players)`.
5. Calls `deck_casino_view.refresh(game)` and switches to the game view.
6. If tutorial was selected, calls `deck_casino_view.start_tutorial()`.

**`_launch_blackjack()`** — prompts for a player name via `QInputDialog`, instantiates `BlackjackGame(player)`, and passes it to `BlackjackView.set_game()` before switching to that view.

**`_launch_baccarat()`** — same pattern: prompts for a name, instantiates `BaccaratGame(player)`, passes it to `BaccaratView.set_game()`.

**Deck Casino action handlers:**
- `_on_deck_casino_take(card, take)` → records `table_before`, calls `game.play_card(card, take)`; shows a warning on `ValueError`; appends a move record; calls `_show_capture_events()`; calls `_after_deck_casino_action()`.
- `_on_deck_casino_place(card)` → calls `game.play_card(card, None)`; appends a move record; calls `_after_deck_casino_action()`.
- `_after_deck_casino_action()` → **auto-plays all consecutive AI turns** in a loop until the round is over or a human player's turn is reached. Also skips over any human whose hand is empty (deck exhausted). Then: checks if the round is over; if yes, calls `game.end_round()` and shows `RoundResultOverlay`. If there is a winner, returns to lobby. If no winner, starts a new round. Always calls `refresh()` and `FileManager.save()` to persist state.

**`_show_capture_events(player, card, take, sweeps_before)`** — detects notable captures and triggers the appropriate overlays:
- Sweep detected (player's sweep count increased) → calls `show_sweep_flash()`.
- Aces, Diamond-10, or Spade-2 in the take → calls `show_point_toast()` with a descriptive title. Hint mode adds an explanatory subtitle.

**Dialogs defined here:**
- `PlayerSetupDialog` — two-mode form (PvP / PvC) with difficulty selection for AI.
- `TutorialModeDialog` — Yes/No prompt for tutorial.
- `SidebarWidget` — shows player name and score.

---

### 5.4 `LobbyView`
**File:** [view/lobby_view.py](view/lobby_view.py)

The game selection screen. Shows three `GameBannerWidget`s (Deck Casino, Blackjack, Baccarat) in a row. Each banner is a `QWidget` with a QPainter-drawn coloured header and card-fan illustration.

All three banners are fully wired — clicking "Play Deck Casino / Blackjack / Baccarat" emits `game_selected("Deck Casino" | "Blackjack" | "Baccarat")`, which is caught by `MainWindow._on_game_selected()`.

| Game        | Header colour | Description shown               |
|-------------|---------------|----------------------------------|
| Deck Casino | Dark green    | Finnish card-taking game with AI opponent |
| Blackjack   | Dark blue     | Beat the dealer to 21 without going bust |
| Baccarat    | Dark purple   | Bet on Punto, Banco or Tie       |

---

### 5.5 `BlackjackView`
**File:** [view/blackjack_view.py](view/blackjack_view.py)

The Blackjack game UI. Holds a `BlackjackGame` reference and drives it directly (no signals back to `MainWindow` for game actions). Emits `back_pressed` to return to the lobby.

**Layout (top to bottom):**
- Title bar with "← Lobby" button and bankroll display
- Dealer zone — `TableZoneWidget` with dealer cards; hole card shown face-down during player phase
- Player zone — `TableZoneWidget` with player cards (active hand during player phase; all hands in dealer/done phase)
- Result label — outcome and payout after round ends
- Action buttons: Hit | Stand | Double Down | Split (enabled only in player phase)
- Bottom row: `BettingPanel` (bet spinner + Deal button) | New Round button (visible only in done phase)

**`BettingPanel`** (helper widget, same file) — shared with `BaccaratView`. Wraps a `QSpinBox` and a button into a horizontal row. Emits `bet_confirmed(int)`.

**`set_game(game)`** — installs a new `BlackjackGame` and resets the view to betting state.

**Interaction flow:**
- "Deal" → `_on_deal(bet)` → `game.start_round(bet)` → `_settle_and_refresh()`
- "Hit" → `game.hit()` → `_settle_and_refresh()`
- "Stand" → `game.stand()` → `_settle_and_refresh()`
- "Double Down" → `game.double_down()` → `_settle_and_refresh()`
- "Split" → `game.split()` → `_settle_and_refresh()`
- "New Round" → creates a fresh `BlackjackGame` with the same player (preserving bankroll)

**`_settle_and_refresh()`** — calls `game.settle_bets()` once when phase reaches `"done"`, then calls `refresh()`.

**`refresh()`** — rebuilds the entire view from game state: dealer cards (hole card face-down in player phase, all revealed in dealer/done), player cards, value labels, button enable states, result text.

---

### 5.6 `BaccaratView`
**File:** [view/baccarat_view.py](view/baccarat_view.py)

The Baccarat (Punto Banco) game UI. Holds a `BaccaratGame` reference. Emits `back_pressed` to return to the lobby. Third-card drawing is shown with a short `QTimer` delay for visual pacing.

**Layout (top to bottom):**
- Title bar with "← Lobby" button and bankroll display
- Side-by-side hand zones: Punto (left) vs Banco (right), each with a `TableZoneWidget`
- Result label — winner, totals, and payout
- Bet type row — radio buttons: Punto (1:1) | Banco (0.95:1) | Tie (8:1)
- Bottom row: `BettingPanel` (shared from `blackjack_view.py`) + New Round button

**`set_game(game)`** — installs a new `BaccaratGame` and resets to betting state.

**Interaction flow:**
1. "Deal" → `_on_deal(bet)` → `game.start_round(bet, bet_type)`
   - If natural: `QTimer(400ms)` → `_finish_round()`
   - Otherwise: `QTimer(800ms)` → `_draw_and_finish()`
2. `_draw_and_finish()` → `game.draw_third_card()` → `_refresh_hands()` → `QTimer(500ms)` → `_finish_round()`
3. `_finish_round()` → `game.get_result()` → `game.settle_bet()` → updates bankroll label, shows result, highlights winner header
4. "New Round" → creates a fresh `BaccaratGame` with the same player

The background is painted dark purple (`#1a1a3a`) to distinguish Baccarat from Blackjack (dark green) and Deck Casino.

---

### 5.7 `DeckCasinoInstructionsDialog`
**File:** [view/game_instructions/deck_casino.py](view/game_instructions/deck_casino.py)

A `QDialog` with a `QTabWidget` containing five tabs of HTML content:

| Tab              | Content                                   |
|------------------|-------------------------------------------|
| How to Play      | Setup, turn actions, multi-group takes, sweep, round end |
| Special Cards    | Dual-value table, example takes           |
| Scoring          | Points table, max-per-round example       |
| Strategies       | 7 named tactical tips                     |
| Example Scenarios| 3 annotated worked examples               |

Each tab is a `QTextBrowser` rendering the HTML string. Opened when the user clicks "How to Play" in `DeckCasinoView`.

---

### 5.8 `DrawnAssets`
**File:** [view/drawn_assets.py](view/drawn_assets.py)

A module of shared QPainter-drawn UI components. Nothing in here uses image files.

#### `make_window_icon(size=64) → QPixmap`
Draws the application window icon: a dark-green rounded square with a gold border ring and all four suit symbols (♠♥♣♦) in their respective quadrants. Used by `MainWindow` to set the window icon.

#### `make_history_icon(kind, size=20) → QPixmap`
Returns a small icon for move-history rows:
- `"take"` — green down-arrow (cards captured)
- `"place"` — blue up-arrow (card placed)
- `"sweep"` — gold 4-point star

#### `AvatarWidget`
Circular badge (default 26 px diameter) showing the first letter of a player's name. Background colour is chosen deterministically from the name hash using an 8-colour palette, so the same player always gets the same colour.

#### `SweepFlashOverlay`
Full-widget translucent overlay that announces a sweep. Placed as a child of `DeckCasinoView`; mouse-transparent so it never blocks interaction.

- **`flash(player_name, hint_text="")`** — fades in to 90% opacity, holds for 1.2 s (1.6 s if hint text is present), then fades out over 480 ms.
- Draws a dark dim layer, a gold radial glow, a large "SWEEP!" headline, the player name, and (in hint mode) an explanatory subtitle.

#### `RoundResultOverlay`
Dark-themed modal `QDialog` displayed after each round or at game end. Shows players ranked by score with a medal indicator (1st / 2nd / 3rd) and a "Continue" or "New Game" button. Used by `MainWindow._after_deck_casino_action()`.

#### `PointToastOverlay`
Small non-blocking animated banner that slides in near the top of the game view to announce a notable card capture (Ace, Diamond-10, Spade-2). Fades out automatically (1.8 s without subtitle, 2.8 s with subtitle). Mouse-transparent.

- **`show_event(title, subtitle="", accent="#ffd700")`** — positions itself relative to its parent, fades in, and starts the hold timer.

---

### 5.9 `PlayerBadgeWidget`
**File:** [view/player_badge_widget.py](view/player_badge_widget.py)

A QPainter-drawn widget (34 px tall) representing one player in the score row of `DeckCasinoView`. Replaces simple `QLabel`s with a richer visual.

**Layout (left → right):**
`[padding] [avatar circle] [⚙ CPU pill?] [name: X pts (+pending) (N sweeps)] ... [EASY|MED|HARD pill?] [padding]`

- The **avatar circle** shows the player's initial letter with a colour derived from the name hash.
- The **"⚙ CPU" pill** (blue-grey) and **difficulty pill** (green/amber/red) are only drawn for AI players.
- The **active player** gets a brighter background and a gold left accent bar.
- **`pending_pts`** — projected points to be awarded at round end, shown in light green after the score. Computed from the player's current collection and passed in at construction time.
- **`is_current`** — `True` for the player whose turn it is.

---

## 6. Entry Point

**File:** [main.py](main.py)

```python
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
```

Creates the Qt application, instantiates `MainWindow` (which builds the full UI and wires all signals), shows the window, and starts the Qt event loop.

---

## 7. Data Flow: A Complete Turn

Here is what happens end-to-end when a player selects a hand card, selects two table cards, and clicks "Take Cards":

```
User clicks hand card
  └── CardWidget.mousePressEvent()
        └── CardWidget.clicked signal
              └── DeckCasinoView._on_hand_card_clicked(card, widget)
                    ├── stores card in _selected_hand_card
                    ├── highlights widget
                    └── calls _update_buttons()  [enables Place Card]

User clicks two table cards
  └── DeckCasinoView._on_table_card_clicked()  (called twice)
        ├── adds cards to _selected_table_cards
        └── calls _update_buttons()  [enables Take Cards]

User clicks "Take Cards"
  └── DeckCasinoView._on_take_clicked()
        └── emits take_requested(hand_card, frozenset({table_card1, table_card2}))

MainWindow._on_deck_casino_take(card, take)
  ├── records table_before and sweeps_before snapshots
  ├── DeckCasinoGame.play_card(card, take)
  │     ├── CasinoTakeAlgorithm.is_valid_take()  [validates the take]
  │     ├── removes table cards from _table_cards
  │     ├── player.add_to_collection([card] + [table_card1, table_card2])
  │     ├── records _last_taker
  │     ├── check_sweep()  [awards sweep if table is empty]
  │     ├── draws one card from stock into player.hand
  │     └── advance_turn()
  ├── FileManager.record_move()  [builds move record with advice tip]
  └── _show_capture_events()
        ├── if sweep: deck_casino_view.show_sweep_flash(player_name, hint_text)
        └── if Ace/D10/S2: deck_casino_view.show_point_toast(title, subtitle, accent)

MainWindow._after_deck_casino_action()
  ├── [AI auto-play loop]
  │     while not round_over and current_player.is_ai:
  │       AIOpponent.decide_action(game, difficulty) → (card, take)
  │       game.play_card(card, take)
  │       _show_capture_events()
  ├── checks game.is_round_over()
  │     └── if True: calls game.end_round() → calculate_scores()
  │           └── RoundResultOverlay(players, is_game_over).exec()
  │                 └── if has_winner(): switch_view(LOBBY), return
  │                     else: game.start_game()  (new round)
  ├── deck_casino_view.refresh(game)
  │     ├── rebuilds PlayerBadgeWidget score row (with pending_pts)
  │     ├── rebuilds table card widgets
  │     ├── rebuilds hand card widgets (the next player's hand)
  │     └── resets all selection state
  └── FileManager.save(game, move_history, player_names)  [persists to roster-keyed JSON]
```
