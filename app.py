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
# TIC-TAC-TOE GAME ENGINE
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
        return [i for i, cell in enumerate(self.board) if cell == EMPTY]

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
        return len(self.available_moves()) == 0 and self.winner() is None

    def game_over(self):
        return self.winner() is not None or self.is_draw()


# ============================================================
# AI IMPLEMENTATIONS
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


class MediumAI:

    def __init__(self, ai_symbol, human_symbol):
        self.ai_symbol = ai_symbol
        self.human_symbol = human_symbol

    def get_move(self, game):
        moves = game.available_moves()
        if not moves:
            return None

        # 1. Win if possible
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

        # 3. Take center
        if 4 in moves:
            return 4

        # 4. Take corner
        corners = [0, 2, 6, 8]
        available_corners = [m for m in corners if m in moves]
        if available_corners:
            return random.choice(available_corners)

        # 5. Random
        return random.choice(moves)


class HardAI:
    """Optimized Minimax with Alpha-Beta pruning and instant opening fast-path."""

    def __init__(self, ai_symbol, human_symbol):
        self.ai_symbol = ai_symbol
        self.human_symbol = human_symbol

    def get_move(self, game):
        moves = game.available_moves()
        if not moves:
            return None

        # Instant fast-paths for early game (eliminates CPU delay)
        if len(moves) == 9:
            return 4  # Center is optimal opening
        if len(moves) == 8:
            if 4 in moves:
                return 4
            return random.choice([0, 2, 6, 8])

        best_score = float("-inf")
        best_move = moves[0]

        for move in moves:
            game.board[move] = self.ai_symbol
            score = self.minimax(game, False, 0, float("-inf"), float("inf"))
            game.board[move] = EMPTY

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def minimax(self, game, maximizing, depth, alpha, beta):
        winner = game.winner()
        if winner == self.ai_symbol:
            return 10 - depth
        if winner == self.human_symbol:
            return depth - 10
        if game.is_draw():
            return 0

        if maximizing:
            max_eval = float("-inf")
            for move in game.available_moves():
                game.board[move] = self.ai_symbol
                score = self.minimax(game, False, depth + 1, alpha, beta)
                game.board[move] = EMPTY
                max_eval = max(max_eval, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for move in game.available_moves():
                game.board[move] = self.human_symbol
                score = self.minimax(game, True, depth + 1, alpha, beta)
                game.board[move] = EMPTY
                min_eval = min(min_eval, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_eval


# ============================================================
# GAME STATE & FACTORIES
# ============================================================

def create_ai(difficulty, ai_symbol, human_symbol):
    if difficulty == "Easy":
        return EasyAI(ai_symbol, human_symbol)
    elif difficulty == "Medium":
        return MediumAI(ai_symbol, human_symbol)
    else:
        return HardAI(ai_symbol, human_symbol)


def create_state(mode="PvE", difficulty="Hard", human_symbol=X):
    ai_symbol = O if human_symbol == X else X
    return {
        "game": TicTacToe(),
        "mode": mode,
        "difficulty": difficulty,
        "human": human_symbol,
        "ai": ai_symbol,
        "current": X,
        "ai_player": create_ai(difficulty, ai_symbol, human_symbol),
        "game_over": False,
        "result": None,
        "winning_cells": [],
        "x_score": 0,
        "o_score": 0,
        "draws": 0
    }


# ============================================================
# SCORE & BOARD DISPLAY
# ============================================================

def score_text(state):
    return (
        "### 🏆 Score\n\n"
        f"❌ X: **{state.get('x_score', 0)}**"
        "  "
        f"🤝 Draws: **{state.get('draws', 0)}**"
        "  "
        f"⭕ O: **{state.get('o_score', 0)}**"
    )


def display(state, message):
    board = state["game"].board
    winning_cells = state.get("winning_cells", [])

    cells = []
    for index, cell in enumerate(board):
        value = cell if cell != EMPTY else " "
        if index in winning_cells:
            value = f"🏆 {value}"
        cells.append(value)

    if state.get("game_over", False):
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
# GAME LIFECYCLE
# ============================================================

def start_new_round(
    state,
    mode,
    difficulty,
    human_symbol,
    preserve_score=True
):
    if not isinstance(state, dict):
        state = create_state(mode, difficulty, human_symbol)

    if preserve_score:
        x_score = state.get("x_score", 0)
        o_score = state.get("o_score", 0)
        draws = state.get("draws", 0)
    else:
        x_score = 0
        o_score = 0
        draws = 0

    new_state = create_state(mode, difficulty, human_symbol)
    new_state["x_score"] = x_score
    new_state["o_score"] = o_score
    new_state["draws"] = draws

    if mode == "PvP":
        new_state["ai"] = None
        new_state["ai_player"] = None
        new_state["current"] = X
        message = "👥 **Player vs Player**\n\n❌ Player X's turn."
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

    # If human chose O, AI starts as X
    ai_move = new_state["ai_player"].get_move(new_state["game"])
    if ai_move is not None:
        new_state["game"].make_move(ai_move, ai_symbol)

    new_state["current"] = human_symbol
    message = (
        "🤖 **Player vs AI**\n\n"
        "You are ⭕ **O**\n\n"
        f"AI is ❌ **X** ({difficulty})\n\n"
        f"🤖 AI placed **{ai_symbol}** at position **{ai_move + 1}**.\n\n"
        "👉 **Your turn!**"
    )
    return display(new_state, message)


def new_board(mode, difficulty, human_symbol, state):
    return start_new_round(state, mode, difficulty, human_symbol, preserve_score=True)

new_game = new_board


def reset_scores(mode, difficulty, human_symbol, state):
    fresh_state = create_state(mode, difficulty, human_symbol)
    return start_new_round(fresh_state, mode, difficulty, human_symbol, preserve_score=False)


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
            "Click **New Board** to play again."
        )
    else:
        message = (
            "🤝 **Final Board**\n\n"
            "This round ended in a draw.\n\n"
            "Click **New Board** to play again."
        )

    return display(state, message)


# ============================================================
# PLAYER MOVE HANDLER
# ============================================================

def player_move(position, state):
    if not isinstance(state, dict):
        state = create_state()

    # Safety: ensure AI is initialized even if state was empty
    if state.get("mode") == "PvE" and state.get("ai_player") is None:
        state["ai_player"] = create_ai(
            state.get("difficulty", "Hard"),
            state.get("ai", O),
            state.get("human", X)
        )

    game = state["game"]

    if state.get("game_over", False):
        return display(
            state,
            "🏁 This round is complete. Click **New Board** to start a new match."
        )

    # PvE: ensure it's human's turn
    if state.get("mode") == "PvE":
        if state.get("current") != state.get("human"):
            return display(state, "🤖 Please wait for the AI to move.")

    player = state.get("current", X)
    success = game.make_move(position, player)

    if not success:
        return display(state, "❌ That cell is already occupied.")

    # Check human win
    if game.winner() == player:
        state["game_over"] = True
        state["result"] = player
        state["winning_cells"] = game.winning_cells()
        if player == X:
            state["x_score"] += 1
        else:
            state["o_score"] += 1
        return display(state, f"🏆 **Player {player} wins!**\n\nClick **New Board** to play again.")

    # Check draw
    if game.is_draw():
        state["game_over"] = True
        state["result"] = "Draw"
        state["winning_cells"] = []
        state["draws"] += 1
        return display(state, "🤝 **It's a Draw!**\n\nClick **New Board** to play again.")

    # PvP switch turn
    if state.get("mode") == "PvP":
        state["current"] = O if player == X else X
        return display(state, f"👉 Player **{state['current']}**'s turn.")

    # PvE - AI Turn
    state["current"] = state["ai"]
    ai = state["ai_player"]
    ai_move = ai.get_move(game)

    if ai_move is None:
        state["game_over"] = True
        state["result"] = "Draw"
        state["draws"] += 1
        return display(state, "🤝 **It's a Draw!**\n\nClick **New Board** to play again.")

    game.make_move(ai_move, state["ai"])

    # Check AI win
    if game.winner() == state["ai"]:
        state["game_over"] = True
        state["result"] = state["ai"]
        state["winning_cells"] = game.winning_cells()
        if state["ai"] == X:
            state["x_score"] += 1
        else:
            state["o_score"] += 1
        return display(state, f"🤖 **AI ({state['ai']}) wins!**\n\nClick **New Board** to play again.")

    # Check AI draw
    if game.is_draw():
        state["game_over"] = True
        state["result"] = "Draw"
        state["winning_cells"] = []
        state["draws"] += 1
        return display(state, "🤝 **It's a Draw!**\n\nClick **New Board** to play again.")

    # Switch back to human
    state["current"] = state["human"]
    return display(
        state,
        (
            f"🤖 AI placed **{state['ai']}** at position **{ai_move + 1}**.\n\n"
            "👉 **Your turn!**"
        )
    )


# ============================================================
# CSS
# ============================================================

css = """
.game-title {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
    margin-bottom: 2px;
}

.subtitle {
    text-align: center;
    color: #888;
    font-size: 15px;
    margin-bottom: 16px;
}

.board-btn {
    min-width: 90px !important;
    min-height: 90px !important;
    font-size: 38px !important;
    font-weight: bold !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 12px !important;
    transition: all 0.2s ease-in-out !important;
}

.board-btn:hover {
    transform: scale(1.02);
}
"""

# ============================================================
# GRADIO INTERFACE
# ============================================================

initial_state = create_state("PvE", "Hard", X)

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
        Player vs Player • Player vs AI (Instant AI Moves)
        </div>
        """
    )

    game_state = gr.State(initial_state)

    with gr.Row():
        # SETTINGS
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Settings")
            mode = gr.Radio(
                ["PvE", "PvP"],
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
                "🎮 New Game",
                variant="primary"
            )
            reset_score_button = gr.Button(
                "🗑️ Reset Scores"
            )

        # BOARD
        with gr.Column(scale=2):
            gr.Markdown("### 🎯 Game Board")
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
                "🤖 **Player vs AI**\n\n"
                "You are ❌ **X** | AI is ⭕ **O** (Hard)\n\n"
                "👉 **Your turn! Click any cell to start.**"
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

    # Mode / Setting change or Start Game
    new_game_button.click(
        fn=new_game,
        inputs=[mode, difficulty, symbol, game_state],
        outputs=outputs
    )

    mode.change(
        fn=new_game,
        inputs=[mode, difficulty, symbol, game_state],
        outputs=outputs
    )

    difficulty.change(
        fn=new_game,
        inputs=[mode, difficulty, symbol, game_state],
        outputs=outputs
    )

    symbol.change(
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
# LAUNCH CONFIGURATION
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting Tic-Tac-Toe on port {port}...")
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )
