from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget,
    QTextBrowser, QDialogButtonBox,
)


_HOW_TO_PLAY = """
<h2>Deck Casino — How to Play</h2>
<p>Collect cards and score points each round.
The first player to reach <b>16 points</b> wins the game.</p>

<h3>Setup</h3>
<ul>
  <li>The deck is shuffled at the start of each round.</li>
  <li>Each player is dealt <b>4 cards</b> (hidden from other players).</li>
  <li><b>4 cards</b> are placed face-up on the table.</li>
  <li>The remaining cards form the face-down <b>stock pile</b>.</li>
</ul>

<h3>On Your Turn</h3>
<ol>
  <li>Click a card in your hand to select it.</li>
  <li>Choose one of two actions:</li>
</ol>
<ul>
  <li><b>Take Cards</b> — click one or more table cards whose values add up to
      your card's hand value, then press <i>Take Cards</i>. You collect all
      selected table cards plus your played card.</li>
  <li><b>Place Card</b> — press <i>Place Card</i> to put your selected card
      face-up on the table. You must place if no valid take exists.</li>
</ul>
<p>After your turn you draw one card from the stock (if it is not empty).</p>

<h3>Taking Multiple Groups at Once</h3>
<p>If your card's value matches multiple <i>non-overlapping</i> groups of table
cards simultaneously, you may take all of them in a single move.</p>
<p><b>Example:</b> You play ♠J (value 11). The table has ♥J (11), ♦6+♣5 (=11),
and ♣10+♠A (=11). All three groups are non-overlapping, so you take all five
table cards at once.</p>

<h3>Sweep</h3>
<p>If your take clears <b>all</b> cards from the table, you score a
<b>Sweep</b> — worth 1 point at round end. The table is then empty and the
next player must place a card.</p>

<h3>End of Round</h3>
<p>The round ends when the stock is empty and all hands are empty.
The last player to take cards collects any cards still on the table.
Points are then tallied and added to each player's cumulative score.</p>
"""

_SPECIAL_CARDS = """
<h2>Special Cards</h2>
<p>Three cards have a higher <b>hand value</b> (used when taking from the table)
than their <b>table value</b> (used when sitting on the table).
This lets them reach multi-card combinations that normal cards cannot.</p>

<table border="1" cellpadding="6" cellspacing="0" width="100%">
  <tr style="background-color:#e8f5e9;">
    <th>Card</th><th>Hand value</th><th>Table value</th><th>Bonus at round end</th>
  </tr>
  <tr>
    <td>&#9830; Diamond-10</td>
    <td align="center">16</td><td align="center">10</td><td align="center">2 pts</td>
  </tr>
  <tr>
    <td>&#9824; Spade-2</td>
    <td align="center">15</td><td align="center">2</td><td align="center">1 pt</td>
  </tr>
  <tr>
    <td>Any Ace (&#215;4)</td>
    <td align="center">14</td><td align="center">1</td><td align="center">1 pt each</td>
  </tr>
</table>

<p>All other cards have the same value in hand and on the table
(2–10, J&#160;=&#160;11, Q&#160;=&#160;12, K&#160;=&#160;13).</p>

<h3>Example Takes Using Special Hand Values</h3>
<ul>
  <li>&#9830;10 (hand 16): takes two 8s, or a 9&#160;+&#160;7, or a 6&#160;+&#160;5&#160;+&#160;5.</li>
  <li>&#9824;2 (hand 15): takes a 9&#160;+&#160;6, or a 7&#160;+&#160;8, or a 5&#160;+&#160;5&#160;+&#160;5.</li>
  <li>Ace (hand 14): takes a 9&#160;+&#160;5, or a 7&#160;+&#160;7, or a 6&#160;+&#160;5&#160;+&#160;3.</li>
</ul>

<p><b>On the table</b>, special cards count at their <i>lower</i> table value.
An Ace on the table is worth only 1, making it trivial to include in a sum but
impossible to take with a single matching card (no standard card has hand value 1).</p>

<p>Special cards are highlighted with a <b style="color:#c8a200;">gold border</b>
in the game.</p>
"""

_SCORING = """
<h2>Scoring</h2>
<p>Points are awarded at the end of each round and added to cumulative totals.
The <b>first player to reach 16 points</b> wins the game.</p>

<table border="1" cellpadding="6" cellspacing="0" width="100%">
  <tr style="background-color:#e8f5e9;">
    <th>Condition</th><th>Points</th><th>Notes</th>
  </tr>
  <tr>
    <td>Each Sweep scored this round</td>
    <td align="center">1 pt each</td>
    <td>Unlimited per round</td>
  </tr>
  <tr>
    <td>Each Ace in your collection</td>
    <td align="center">1 pt each</td>
    <td>Up to 4 pts from aces alone</td>
  </tr>
  <tr>
    <td>Most cards collected</td>
    <td align="center">1 pt</td>
    <td>No award on a tie</td>
  </tr>
  <tr>
    <td>Most Spades collected</td>
    <td align="center">2 pts</td>
    <td>No award on a tie</td>
  </tr>
  <tr>
    <td>&#9830; Diamond-10 in collection</td>
    <td align="center">2 pts</td>
    <td>Awarded to whoever holds it</td>
  </tr>
  <tr>
    <td>&#9824; Spade-2 in collection</td>
    <td align="center">1 pt</td>
    <td>Awarded to whoever holds it</td>
  </tr>
</table>

<h3>Maximum Points in One Round</h3>
<p>A single player could theoretically earn:
sweeps&#160;+ 4 (all aces) + 1 (most cards) + 2 (most spades)
+ 2 (&#9830;10) + 1 (&#9824;2) = <b>10+ points</b> in one round.</p>
<p>In a typical two-player round, 7–10 points are distributed in total.</p>

<h3>Quick Route to 16</h3>
<p>The fastest path is to dominate two or three categories every round rather
than winning them all once. Consistently winning <i>most spades</i> (2 pts) and
<i>Diamond-10</i> (2 pts) alone adds 4 points per round — reaching 16 in just
four rounds.</p>
"""

_STRATEGIES = """
<h2>Winning Strategies</h2>

<h3>1. Hunt for Sweeps</h3>
<p>A sweep clears the table, scores 1 point, and denies opponents all those
cards. Watch the table: when few cards remain and their total matches a card in
your hand, prioritise the sweep over a smaller take.</p>

<h3>2. Secure Diamond-10 and Spade-2</h3>
<p>&#9830;10 (2 pts) and &#9824;2 (1 pt) are fixed bonuses — whoever collects
them gets the points outright. Use your own high-value special cards to take them
off the table before an opponent can. Leaving them on the table is a gift.</p>

<h3>3. Collect Aces Aggressively</h3>
<p>Each Ace scores 1 point. Because an Ace's table value is only 1, it is
nearly impossible to take it off the table with a single card — but it is easy
to include in a sum-based take. Use your own Ace (hand value 14) to take
multi-card combinations that happen to include an opponent's tabled Ace.</p>

<h3>4. Race for Most Spades (2 pts)</h3>
<p>Most spades is the single highest bonus (2 pts). There are 13 spades in the
deck. Track how many each player is collecting, and when a spade sits on the
table and you have any card that can take it, consider taking it even if a
non-spade take would yield more cards.</p>

<h3>5. Don't Gift Sweeps to Opponents</h3>
<p>Avoid placing a card that leaves just one card (or a simple matching pair) on
an otherwise empty table — this hands an opponent an easy sweep.
When you must place, choose a card whose value is <i>hard</i> to match with the
table's current state.</p>

<h3>6. Exploit Special Card Hand Values</h3>
<p>Aces (14), &#9824;2 (15), and &#9830;10 (16) can reach multi-card
combinations no normal card can. Save these for turns when you can take three or
more table cards at once — a large single take drives the card-count lead and
may create a sweep.</p>

<h3>7. End-of-Round Tactics</h3>
<p>As the stock empties, count your and your opponents' card totals.
If you are close to the card-count lead, aim to take on every turn.
If you lead in spades but an opponent is catching up, prioritise taking any
spade from the table over a slightly larger non-spade take.</p>
"""

_SCENARIOS = """
<h2>Example Scenarios</h2>

<h3>Scenario 1 — Choosing Your Best Take</h3>
<p><b>Table:</b> &#9830;6, &#9827;5, &#9825;J (11), &#9824;A (1), &#9827;10, &#9827;3</p>
<p><b>Your hand:</b> &#9825;Q (12), &#9827;4, &#9830;2, &#9824;J (11)</p>

<p><b>With &#9825;Q (value 12):</b></p>
<ul>
  <li>&#9824;J (11) + &#9824;A (1) = 12 &#10003;</li>
  <li>&#9830;6 + &#9827;5 + &#9824;A (1) = 12 &#10003;</li>
  <li>Both groups share the Ace — they cannot be taken together.</li>
  <li><b>Best pick:</b> &#9824;J + &#9824;A — you collect the Ace (1 pt) and
      remove a high-value spade from the table.</li>
</ul>

<p><b>With &#9824;J (value 11):</b></p>
<ul>
  <li>&#9830;6 + &#9827;5 = 11 &#10003;</li>
  <li>&#9825;J (11) = 11 &#10003;</li>
  <li>&#9827;10 + &#9824;A (1) = 11 &#10003;</li>
  <li>All three groups are non-overlapping — take all five table cards at once.</li>
  <li><b>Result: SWEEP (+1 pt)</b> plus all five cards go to your collection.</li>
</ul>

<h3>Scenario 2 — Using Diamond-10 Strategically</h3>
<p><b>Table:</b> &#9825;8, &#9830;8, &#9827;6, &#9824;5, &#9827;3</p>
<p><b>You hold:</b> &#9830;10 (hand value 16)</p>
<ul>
  <li>&#9825;8 + &#9830;8 = 16 &#10003;</li>
  <li>&#9827;6 + &#9824;5 + &#9827;3 = 14 &#10007; — does not match 16</li>
  <li><b>Take &#9825;8 + &#9830;8.</b> You collect two cards and keep the
      &#9830;10 bonus (2 pts at round end).</li>
  <li><b>Alternative:</b> if the table had &#9825;8 + &#9830;5 + &#9827;3 (=16)
      as well, you could take all five cards in one move.</li>
</ul>

<h3>Scenario 3 — Avoiding a Gift Sweep</h3>
<p><b>Table:</b> &#9827;9, &#9824;4 (two cards, total 13)</p>
<p><b>Your hand:</b> &#9830;7, &#9824;K (13), &#9825;2, &#9827;5</p>
<ul>
  <li>&#9824;K (value 13) could take &#9827;9 + &#9824;4 = 13 — a clean take.</li>
  <li>After taking, the table is empty. The next player <b>must place</b> a card,
      giving the player after them a possible sweep — but <i>you</i> control what
      gets placed on your own subsequent turns.</li>
  <li><b>Placing instead:</b> If you placed &#9825;2 (value 2) on the existing
      table, the new table is &#9827;9, &#9824;4, &#9825;2. A player holding a
      card worth 15 (&#9824;2 hand value) could sweep. Avoid this if an opponent
      might hold &#9824;2.</li>
  <li><b>Rule of thumb:</b> when the table total after your placement would be an
      Ace-14, &#9824;2-15, or &#9830;10-16 equivalent, an opponent with a special
      card can sweep immediately.</li>
</ul>
"""

_TABS = [
    ("How to Play",       _HOW_TO_PLAY),
    ("Special Cards",     _SPECIAL_CARDS),
    ("Scoring",           _SCORING),
    ("Strategies",        _STRATEGIES),
    ("Example Scenarios", _SCENARIOS),
]


class DeckCasinoInstructionsDialog(QDialog):
    """Tabbed instructions dialog for Deck Casino."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("How to Play — Deck Casino")
        self.setMinimumSize(620, 500)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        tab_widget = QTabWidget()
        for title, html in _TABS:
            browser = QTextBrowser()
            browser.setHtml(html)
            browser.setOpenExternalLinks(False)
            tab_widget.addTab(browser, title)

        layout.addWidget(tab_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
