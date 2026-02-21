# Y2_2026_83758_casino_game

## UML Diagrams
[Link to .xml file UML diagram visualiser](https://gitmanager.cs.aalto.fi/static/CS-A1121_2026Autumn/_static/mxgraph_mini/javascript/examples/grapheditor/www/index.html)


## Description
A comprehensive casino card game application featuring multiple classic card games including Deck Casino (Kasino Kortipelli), Blackjack, and Baccarat. This project implements a full GUI application with AI opponents, betting systems, and game state persistence.

The application provides an interactive gaming experience with three main card games:

- **Deck Casino (Kasino Kortipelli)**: A trick-taking card game where players capture cards from the table by matching ranks or building combinations
- **Blackjack**: The classic card game where players aim to get as close to 21 as possible without going over
- **Baccarat**: A comparing card game between the player's hand (Punto) and the banker's hand (Banco)

Key features include:
- Graphical user interface built with PyQt6
- AI opponents with configurable difficulty levels
- Betting system with bankroll management
- Game state saving and loading
- Session statistics tracking
- Multiple player support


## Visuals
The application includes several views:
- Lobby view for game selection and player setup
- Individual game views with card animations and interactive elements
- Score displays and betting interfaces

## Installation
### Prerequisites
- Python 3.8 or higher
- PyQt6 for the GUI components

### Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install PyQt6
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage
1. Launch the application
2. Select a game from the lobby
3. Configure players (human or AI)
4. Set betting parameters if applicable
5. Play the game following the on-screen instructions

### Game Rules
- **Cassino**: Players take turns playing cards and capturing combinations from the table
- **Blackjack**: Hit, stand, double down, or split to beat the dealer
- **Baccarat**: Bet on Punto, Banco, or Tie and watch the automated dealing

## Authors and acknowledgment
Project developed for Aalto University CS-A1123 Basics in Programming Y2 course, Spring 2026.
