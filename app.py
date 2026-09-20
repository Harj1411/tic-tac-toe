import os
import random
import gradio as gr

# ============================================================
# CONSTANTS
# ============================================================

X = "X"
O = "O"
EMPTY = ""


# ============================================================
# TIC-TAC-TOE GAME
# ============================================================

class TicTacToe:

    WINNING_COMBINATIONS = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6)
    ]

    def __init__(self):
        self.board = [EMPTY] * 9

    def reset(self):
        self.board = [EMPTY] * 9

    def available_moves(self):
        return [
            i
            for i, cell in enumerate(self.board)
            if cell == EMPTY
        ]

    def make_move(self, position, player):
        if position < 0 or position > 8:
            return False

        if self.board[position] != EMPTY:
            return False

        self.board[position] = player
        return True

    def winner(self):
        for a, b, c in self.WINNING_COMBINATIONS:
            if (
                self.board[a] != EMPTY
                and self.board[a] == self.board[b]
                and self.board[b] == self.board[c]
            ):
                return self.board[a]
        return None

    def winning_cells(self):
        for a, b, c in self.WINNING_COMBINATIONS:
            if (
                self.board[a] != EMPTY
                and self.board[a] == self.board[b]
                and self.board[b] == self.board[c]
            ):
                return [a, b, c]
        return []

    def is_draw(self):
        return (
            len(self.available_moves()) == 0
            and self.winner() is None
        )

    def game_over(self):
        return (
            self.winner() is not None
            or self.is_draw()
        )


# ============================================================
# EASY AI
# ============================================================

class EasyAI:

    def __init__(self, ai_symbol, human_symbol):
        self.ai_symbol = ai_symbol
        self.human_symbol = human_symbol

    def get_move(self, game):
        moves = game.available_moves()
        if not moves:
            return None
        return random.choice(moves)


# ============================================================
# MEDIUM AI
# ============================================================

class MediumAI:

    def __init__(self, ai_symbol, human_symbol):
        self.ai_symbol = ai_symbol
        self.human_symbol = human_symbol

    def get_move(self, game):
        moves = game.available_moves()
        if not moves:
            return None

        # 1. AI can win
        for move in moves:
            game.board[move] = self.ai_symbol
            if game.winner() == self.ai_symbol:
                game.board[move] = EMPTY
                return move
            game.board[move] = EMPTY

        # 2. Block human
        for move in moves:
            game.board[move] = self.human_symbol
            if game.winner() == self.human_symbol:
                game.board[move] = EMPTY
                return move
            game.board[move] = EMPTY

        # 3. Center
        if 4 in moves:
            return 4

        # 4. Corner
        corners = [0, 2, 6, 8]
        available_corners = [
            move for move in corners
            if move in moves
        ]
        if available_corners:
            return random.choice(available_corners)

        # 5. Random
        return random.choice(moves)


# ============================================================
# HARD AI - MINIMAX
# ============================================================

class HardAI:

    def __init__(self, ai_symbol, human_symbol):
        self.ai_symbol = ai_symbol
        self.human_symbol = human_symbol

    def get_move(self, game):
        moves = game.available_moves()
        if not moves:
            return None

        best_score = float("-inf")
        best_move = moves[0]

        for move in moves:
            game.board[move] = self.ai_symbol
            score = self.minimax(game, False, 0)
            game.board[move] = EMPTY

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def minimax(self, game, maximizing, depth):
        winner = game.winner()

        if winner == self.ai_symbol:
            return 10 - depth

        if winner == self.human_symbol:
            return depth - 10

        if game.is_draw():
            return 0

        if maximizing:
            best_score = float("-inf")
            for move in game.available_moves():
                game.board[move] = self.ai_symbol
                score = self.minimax(game, False, depth + 1)
                game.board[move] = EMPTY
                best_score = max(best_score, score)
            return best_score
        else:
            best_score = float("inf")
            for move in game.available_moves():
                game.board[move] = self.human_symbol
                score = self.minimax(game, True, depth + 1)
                game.board[move] = EMPTY
                best_score = min(best_score, score)
            return best_score


# ============================================================
# GAME STATE
# ============================================================

def create_state():
    return {
        "game": TicTacToe(),
        "mode": "PvE",
        "difficulty": "Hard",
        "human": X,
        "ai": O,
        "current": X,
        "ai_player": None,
        "game_over": False,
        "result": None,
        "winning_cells": [],
        "x_score": 0,
        "o_score": 0,
        "draws": 0
    }


# ============================================================
# CREATE AI
# ============================================================

def create_ai(difficulty, ai_symbol, human_symbol):
    if difficulty == "Easy":
        return EasyAI(ai_symbol, human_symbol)
    elif difficulty == "Medium":
        return MediumAI(ai_symbol, human_symbol)
    else:
        return HardAI(ai_symbol, human_symbol)


# ============================================================
# SCORE DISPLAY
# ============================================================

def score_text(state):
    return (
        "### 🏆 Score\n\n"
        f"❌ X: **{state['x_score']}**"
        "  "
        f"🤝 Draws: **{state['draws']}**"
        "  "
        f"⭕ O: **{state['o_score']}**"
    )


# ============================================================
# BOARD DISPLAY
# ============================================================

def display(state, message):
    board = state["game"].board
    winning_cells = state.get("winning_cells", [])

    cells = []
    for index, cell in enumerate(board):
        value = cell if cell != EMPTY else " "
        if index in winning_cells:
            value = f"🏆 {value}"
        cells.append(value)

    if state["game_over"]:
        new_board_visible = gr.update(visible=True)
        show_winner_visible = gr.update(visible=True)
    else:
        new_board_visible = gr.update(visible=False)
        show_winner_visible = gr.update(visible=False)

    return (
        *cells,
        message,
        score_text(state),
        state,
        new_board_visible,
        show_winner_visible
    )


# ============================================================
# START NEW ROUND
# ============================================================

def start_new_round(
    state,
    mode,
    difficulty,
    human_symbol,
    preserve_score=True
):
    if preserve_score:
        x_score = state.get("x_score", 0)
        o_score = state.get("o_score", 0)
        draws = state.get("draws", 0)
    else:
        x_score = 0
        o_score = 0
        draws = 0

    new_state = create_state()
    new_state["mode"] = mode
    new_state["difficulty"] = difficulty
    new_state["human"] = human_symbol
    new_state["x_score"] = x_score
    new_state["o_score"] = o_score
    new_state["draws"] = draws
    new_state["game_over"] = False
    new_state["result"] = None
    new_state["winning_cells"] = []

    if mode == "PvP":
        new_state["ai"] = None
        new_state["ai_player"] = None
        new_state["current"] = X
        message = (
            "👥 **Player vs Player**\n\n"
            "❌ Player X's turn."
        )
        return display(new_state, message)

    # PvE
    ai_symbol = O if human_symbol == X else X
    new_state["ai"] = ai_symbol
    new_state["ai_player"] = create_ai(difficulty, ai_symbol, human_symbol)

    if human_symbol == X:
        new_state["current"] = X
        message = (
            "🤖 **Player vs AI**\n\n"
            "You are ❌ **X**\n\n"
            f"AI is ⭕ **O** ({difficulty})\n\n"
            "👉 **Your turn!**"
        )
        return display(new_state, message)

    ai_move = new_state["ai_player"].get_move(new_state["game"])
    if ai_move is not None:
        new_state["game"].make_move(ai_move, ai_symbol)

    new_state["current"] = human_symbol
    message = (
        "🤖 **Player vs AI**\n\n"
        "You are ⭕ **O**\n\n"
        f"AI is ❌ **X** ({difficulty})\n\n"
        "🤖 AI made the first move.\n\n"
        "👉 **Your turn!**"
    )
    return display(new_state, message)


# ============================================================
# NEW BOARD & NEW GAME BUTTONS
# ============================================================

def new_board(mode, difficulty, human_symbol, state):
    return start_new_round(
        state,
        mode,
        difficulty,
        human_symbol,
        preserve_score=True
    )

new_game = new_board


# ============================================================
# RESET SCORES
# ============================================================

def reset_scores(mode, difficulty, human_symbol, state):
    fresh_state = create_state()
    fresh_state["x_score"] = 0
    fresh_state["o_score"] = 0
    fresh_state["draws"] = 0
    return start_new_round(
        fresh_state,
        mode,
        difficulty,
        human_symbol,
        preserve_score=False
    )


# ============================================================
# SHOW WINNING BOARD
# ============================================================

def show_winning_board(state):
    if not isinstance(state, dict):
        state = create_state()

    winner = state.get("result")
    winning_cells = state.get("winning_cells", [])

    if winner in [X, O]:
        state["winning_cells"] = winning_cells
        message = (
            f"🏆 **Winning Board**\n\n"
            f"Player **{winner}** won this round.\n\n"
            "The winning cells are highlighted with 🏆.\n\n"
            "Click **New Board** when you are ready."
        )
    else:
        message = (
            "🤝 **Final Board**\n\n"
            "This round ended in a draw.\n\n"
            "Click **New Board** when you are ready."
        )

    return display(state, message)


# ============================================================
# PLAYER MOVE
# ============================================================

def player_move(position, state):
    if not isinstance(state, dict):
        state = create_state()

    game = state["game"]

    if state["game_over"]:
        return display(
            state,
            "🏁 This round is complete. "
            "Choose **New Board** or "
            "**Show Winning Board**."
        )

    if state["mode"] == "PvE":
        if state["current"] != state["human"]:
            return display(state, "🤖 Please wait for the AI.")

    player = state["current"]
    success = game.make_move(position, player)

    if not success:
        return display(state, "❌ That cell is already occupied.")

    if game.winner() == player:
        state["game_over"] = True
        state["result"] = player
        state["winning_cells"] = game.winning_cells()

        if player == X:
            state["x_score"] += 1
        else:
            state["o_score"] += 1

        message = (
            f"🏆 **Player {player} wins!**\n\n"
            "What would you like to do?"
        )
        return display(state, message)

    if game.is_draw():
        state["game_over"] = True
        state["result"] = "Draw"
        state["winning_cells"] = []
        state["draws"] += 1
        message = (
            "🤝 **It's a Draw!**\n\n"
            "What would you like to do?"
        )
        return display(state, message)

    if state["mode"] == "PvP":
        state["current"] = O if player == X else X
        return display(state, f"👉 Player **{state['current']}**'s turn.")

    # PvE - AI turn
    state["current"] = state["ai"]
    ai = state["ai_player"]
    ai_move = ai.get_move(game)

    if ai_move is None:
        state["game_over"] = True
        state["result"] = "Draw"
        state["draws"] += 1
        return display(state, "🤝 **It's a Draw!**\n\nWhat would you like to do?")

    game.make_move(ai_move, state["ai"])

    if game.winner() == state["ai"]:
        state["game_over"] = True
        state["result"] = state["ai"]
        state["winning_cells"] = game.winning_cells()

        if state["ai"] == X:
            state["x_score"] += 1
        else:
            state["o_score"] += 1

        message = (
            f"🤖 **AI ({state['ai']}) wins!**\n\n"
            "What would you like to do?"
        )
        return display(state, message)

    if game.is_draw():
        state["game_over"] = True
        state["result"] = "Draw"
        state["winning_cells"] = []
        state["draws"] += 1
        return display(
            state,
            "🤝 **It's a Draw!**\n\nWhat would you like to do?"
        )

    state["current"] = state["human"]
    return display(
        state,
        (
            f"🤖 AI placed **{state['ai']}** "
            f"at position **{ai_move + 1}**.\n\n"
            "👉 **Your turn!**"
        )
    )


# ============================================================
# CSS
# ============================================================

css = """
.game-title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #888;
    margin-bottom: 20px;
}

.board-btn {
    min-width: 90px !important;
    min-height: 90px !important;
    font-size: 38px !important;
    font-weight: bold !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
"""

# ============================================================
# GRADIO APP
# ============================================================

with gr.Blocks(
    title="Tic-Tac-Toe",
    css=css
) as app:

    gr.Markdown(
        """
        <div class="game-title">
        🎮 TIC-TAC-TOE
        </div>

        <div class="subtitle">
        Player vs Player • Player vs AI
        </div>
        """
    )

    game_state = gr.State(create_state())

    with gr.Row():
        # SETTINGS
        with gr.Column(scale=1):
            gr.Markdown("## ⚙️ Settings")
            mode = gr.Radio(
                ["PvP", "PvE"],
                value="PvE",
                label="Game Mode"
            )
            difficulty = gr.Radio(
                ["Easy", "Medium", "Hard"],
                value="Hard",
                label="AI Difficulty"
            )
            symbol = gr.Radio(
                ["X", "O"],
                value="X",
                label="Your Symbol"
            )
            new_game_button = gr.Button(
                "🎮 Start Game",
                variant="primary"
            )
            reset_score_button = gr.Button(
                "🗑️ Reset Scores"
            )

        # BOARD
        with gr.Column(scale=2):
            gr.Markdown("## 🎯 Game Board")
            board_buttons = []

            for row in range(3):
                with gr.Row():
                    for column in range(3):
                        position = row * 3 + column
                        button = gr.Button(
                            " ",
                            elem_classes=["board-btn"]
                        )
                        board_buttons.append(button)

            status = gr.Markdown(
                "Click **Start Game** to begin."
            )

            score = gr.Markdown(
                "### 🏆 Score\n\n"
                "❌ X: **0**  "
                "🤝 Draws: **0**  "
                "⭕ O: **0**"
            )

            with gr.Row():
                new_board_button = gr.Button(
                    "🔄 New Board",
                    visible=False,
                    variant="primary"
                )
                show_winning_button = gr.Button(
                    "👀 Show Winning Board",
                    visible=False
                )

    outputs = [
        *board_buttons,
        status,
        score,
        game_state,
        new_board_button,
        show_winning_button
    ]

    new_game_button.click(
        fn=new_game,
        inputs=[mode, difficulty, symbol, game_state],
        outputs=outputs
    )

    new_board_button.click(
        fn=new_board,
        inputs=[mode, difficulty, symbol, game_state],
        outputs=outputs
    )

    show_winning_button.click(
        fn=show_winning_board,
        inputs=[game_state],
        outputs=outputs
    )

    reset_score_button.click(
        fn=reset_scores,
        inputs=[mode, difficulty, symbol, game_state],
        outputs=outputs
    )

    for position, button in enumerate(board_buttons):
        button.click(
            fn=player_move,
            inputs=[gr.State(position), game_state],
            outputs=outputs
        )


# ============================================================
# LAUNCH FOR PRODUCTION / RENDER
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting Tic-Tac-Toe on port {port}...")
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )
