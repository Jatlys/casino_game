# Casino card game (in English)
Implement a casino card game either as a text-based or graphical version. The version to be implemented is the so-called ”deck casino”. Casino enthusiasts note: there exists also other casino rules versions. Implementing these in addition to the base requirements presented here is of course allowed. In this project, the version presented below is implemented first, however.

## The game’s rules
Points are collected during a game, and they are calculated at the end of each round.

A game continues until one of the players gets to 16 points.

## A game round
The deck is shuffled at the end of each round, and the dealer deals each player 4 cards (not visible to others) and 4 cards to the table (visible to everyone). The remaining cards are left upside-down on the table in a stack.

The player after the dealer starts the game. In the next round this player is the dealer.

## What each player does on a turn
- A player can use a card in hand: either take cards from the table with it or put the card onto the table. If the player cannot take any cards from the table, he must put one of his cards on the table.

- If a player takes cards from the table, he collects them for himself in a stack. When the cards run out, points are calculated from this stack.

- The amount of cards in the table can vary freely. If someone for example takes all the cards, the next player has to put one of her cards on the empty table.

- Everytime a player has used a card, he takes a new card to his hand from the deck, so that there are always 4 cards in his hand. (When the deck on the table runs out, no more cards will be taken, and the game continues as long as someone has cards in hand. In this case less than 4 cards is of course possible situation.)

- With a card, player can take one or more cards with the same value from the table, and cards, whose sum is equal to the card that is used to take them. The following example makes this more clear:

**Example**

There are six cards on the table:

| Diamond-6 | Club-5 | Jack of hearts-11 | Ace of spades (1) | Club-10 | Club-3 |

The player has the following cards in hand:

| Queen of hearts (12) | Club-4 | Diamond-2 | Jack of spades (11) | 

1. With the Queen of hearts (12), a player can take the following cards from the table:

Jack of spades (11) + Ace of spades (1) = 12

or

Diamond-6 + Club-5 + Ace of spades (1) = 12

(both cannot be taken, because they contain the same card (Ace of spades))

2. With the card Club-4 the player can take Jack of spades and Club-3

3. With the card Diamond-2 the player gets nothing from the table

4. With the Jack of spades (11) the player gets the following cards:

Diamond-6 + Club-5 = 11

and

Jack of hearts (11) = 11

and

Club-10 + Jack of spades = 11

Thus in this situation the player should choose the jack of spades, so he gets the card he played (jack of spades) and the five cards he takes from the table. After this only the Club-3 remains on the table.

## Sweep
If a player gets all the cards from the table at once, this player gets a so-called sweep, which is written down for point calculation.

## Special cards
- There are a few cards in the game, whose value in hand is bigger than on the table:
    - Aces : in hand 14, on table 1
    - Diamond-10 : in hand 16, on table 10
    - Spade-2 : in hand 15, on table 2
- e.g. : With a diamond-10 a player can take for example two 8’s.
- The values of other cards are the same in hand and on table.

## Point calculation
When everyone runs out of cards, the last player who took cards from the table gets the remaining cards from the table. After this, the points are counted and they are added to previous points.

The following things provide points:

- Every sweep gives 1 point
- Every ace gives 1 point
- The player with most cards gets 1 point
- The player with most spades gets 2 points
- The player with Diamond-10 gets 2 points
- The player with Spade-2 gets 1 point

## Libraries
Not allowed: PyGame, Qt Designer, NumPy, MatPlotLib, Pickle

PyQt is allowed. All other libraries have to be discussed beforehand in the planning phase and agreed upon with the project assistant.

## Requirements
### Easy
- Basic rules implemented (given above)
- Character-based user interface
- 2 - N players
- Perfectly working algorithm that checks the cards taken from the table. Explain your algorithm in detail already in the plan! The algorithm must be able to infer the validity of the cards taken from the table without the user telling how the cards should be comprehended.
- Saving and loading of the current points of the players. Come up with a reasonable file format.
- At least one unit test

### Medium
- All the easy level requirements
- Graphical user interface
- The saving and loading of a game situation must be possible at any point of a game. A saving keeps account of the whole game situation (cards, points, and so on).
- Unit tests for at least some part of the program

### Hard
- All the medium level requirements
- Possibility to play against 0 - N simple computer opponents. The computer opponent must have some sort of a strategy, and not just take anything that is available on the table. Easy sweeps should not be left on the table, and so on. One’s own cards’ later usage can be tried to be improved by putting suitable cards etc. Test different computer opponents against each other!