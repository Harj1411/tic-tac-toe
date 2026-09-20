import os
import random
import gradio as gr

# ============================================================
# CONSTANTS
# ============================================================

X = "X"
O = "O"
EMPTY = ""

WINNING_COMBINATIONS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
    (0, 4, 8), (2, 4, 6)              # Diagonals
]


# ============================================================
# PURE LOGIC (100% SERIALIZABLE)
# ============================================================

def check_winner(board):
    for a, b, c in WINNING_COMBINATIONS:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    return None


def get_winning_cells(board):
    for a, b, c in WINNING_COMBINATIONS:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return [a, b, c]
    return []


def get_available_moves(board):
    return [i for i, cell in enumerate(board) if cell == EMPTY]


def is_board_full(board):
    return len(get_available_moves(board)) == 0


# ============================================================
# AI ENGINE
# ============================================================

def get_ai_move(board, difficulty, ai_symbol, human_symbol):
    moves = get_available_moves(board)
    if not moves:
        return None

    if difficulty == "Easy":
        return random.choice(moves)

    if difficulty == "Medium":
        # 1. Win if available
        for m in moves:
            board[m] = ai_symbol
            if check_winner(board) == ai_symbol:
                board[m] = EMPTY
                return m
            board[m] = EMPTY

        # 2. Block human win
        for m in moves:
            board[m] = human_symbol
            if check_winner(board) == human_symbol:
                board[m] = EMPTY
                return m
            board[m] = EMPTY

        # 3. Center
        if 4 in moves:
            return 4

        # 4. Corners
        corners = [m for m in [0, 2, 6, 8] if m in moves]
        if corners:
            return random.choice(corners)

        return random.choice(moves)

    # ----------------------------------------------------
    # Hard AI: Alpha-Beta Minimax with fast openings
    # ----------------------------------------------------
    if len(moves) == 9:
        return 4  # Center is optimal opening
    if len(moves) == 8:
        if 4 in moves:
            return 4
        return random.choice([0, 2, 6, 8])

    best_score = float("-inf")
    best_move = moves[0]

    for m in moves:
        board[m] = ai_symbol
        score = minimax(board, False, 0, float("-inf"), float("inf"), ai_symbol, human_symbol)
        board[m] = EMPTY
        if score > best_score:
            best_score = score
            best_move = m

    return best_move


def minimax(board, maximizing, depth, alpha, beta, ai_symbol, human_symbol):
    w = check_winner(board)
    if w == ai_symbol:
        return 10 - depth
    if w == human_symbol:
        return depth - 10

    moves = get_available_moves(board)
    if not moves:
        return 0

    if maximizing:
        max_eval = float("-inf")
        for m in moves:
            board[m] = ai_symbol
            score = minimax(board, False, depth + 1, alpha, beta, ai_symbol, human_symbol)
            board[m] = EMPTY
            max_eval = max(max_eval, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float("inf")
        for m in moves:
            board[m] = human_symbol
            score = minimax(board, True, depth + 1, alpha, beta, ai_symbol, human_symbol)
            board[m] = EMPTY
            min_eval = min(min_eval, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_eval


# ============================================================
# STATE FACTORY (NO CUSTOM CLASSES, 100% JSON SERIALIZABLE)
# ============================================================

def create_state(mode="PvE", difficulty="Hard", human_symbol=X):
    ai_symbol = O if human_symbol == X else X
    return {
        "board": [EMPTY] * 9,
        "mode": mode,
        "difficulty": difficulty,
        "human": human_symbol,
        "ai": ai_symbol,
        "current": X,
        "game_over": False,
        "result": None,
        "winning_cells": [],
        "x_score": 0,
        "o_score": 0,
        "draws": 0
    }


# ============================================================
# UI RENDERER
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
    board = state.get("board", [EMPTY] * 9)
    winning_cells = state.get("winning_cells", [])

    cells = []
    for index, cell in enumerate(board):
        value = cell if cell != EMPTY else " "
        if index in winning_cells:
            value = f"🏆 {value}"
        cells.append(value)

    game_over = state.get("game_over", False)
    new_board_visible = gr.update(visible=game_over)
    show_winner_visible = gr.update(visible=game_over)

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

def start_new_round(state, mode, difficulty, human_symbol, preserve_score=True):
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
        new_state["current"] = X
        message = "👥 **Player vs Player**\n\n❌ Player X's turn."
        return display(new_state, message)

    # PvE
    ai_symbol = O if human_symbol == X else X
    new_state["ai"] = ai_symbol

    if human_symbol == X:
        new_state["current"] = X
        message = (
            "🤖 **Player vs AI**\n\n"
            f"You are ❌ **X** | AI is ⭕ **O** ({difficulty})\n\n"
            "👉 **Your turn! Click any square to move.**"
        )
        return display(new_state, message)

    # If human chose O, AI plays first as X
    ai_first_move = get_ai_move(new_state["board"], difficulty, ai_symbol, human_symbol)
    if ai_first_move is not None:
        new_state["board"][ai_first_move] = ai_symbol

    new_state["current"] = human_symbol
    message = (
        "🤖 **Player vs AI**\n\n"
        f"You are ⭕ **O** | AI is ❌ **X** ({difficulty})\n\n"
        f"🤖 AI played at square **{ai_first_move + 1}**.\n\n"
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
            f"Player **{winner}** won this round!\n\n"
            "Winning cells are marked with 🏆.\n\n"
            "Click **New Board** to start a new match."
        )
    else:
        message = (
            "🤝 **Final Board**\n\n"
            "This match ended in a draw!\n\n"
            "Click **New Board** to start a new match."
        )

    return display(state, message)


# ============================================================
# PLAYER MOVE (ATOMIC, NON-BLOCKING)
# ============================================================

def player_move(position, state):
    if not isinstance(state, dict) or "board" not in state:
        state = create_state()

    board = state["board"]

    # 1. Ignore if game already ended
    if state.get("game_over", False):
        return display(state, "🏁 Round is complete. Click **New Board** to play again.")

    # 2. Check valid square
    if position < 0 or position > 8 or board[position] != EMPTY:
        return display(state, "⚠️ That square is already taken. Click an empty square.")

    # 3. PvP Mode
    if state.get("mode") == "PvP":
        curr = state.get("current", X)
        board[position] = curr
        winner = check_winner(board)
        if winner:
            state["game_over"] = True
            state["result"] = winner
            state["winning_cells"] = get_winning_cells(board)
            state["x_score" if winner == X else "o_score"] += 1
            return display(state, f"🏆 **Player {winner} wins!** Click **New Board** to play again.")

        if is_board_full(board):
            state["game_over"] = True
            state["result"] = "Draw"
            state["draws"] += 1
            return display(state, "🤝 **It's a Draw!** Click **New Board** to play again.")

        state["current"] = O if curr == X else X
        return display(state, f"👉 Player **{state['current']}**'s turn.")

    # 4. PvE Mode
    human = state.get("human", X)
    ai = state.get("ai", O)
    diff = state.get("difficulty", "Hard")

    # Place human move
    board[position] = human
    winner = check_winner(board)
    if winner == human:
        state["game_over"] = True
        state["result"] = human
        state["winning_cells"] = get_winning_cells(board)
        state["x_score" if human == X else "o_score"] += 1
        return display(state, f"🎉 **You ({human}) won!** Click **New Board** to play again.")

    if is_board_full(board):
        state["game_over"] = True
        state["result"] = "Draw"
        state["draws"] += 1
        return display(state, "🤝 **It's a Draw!** Click **New Board** to play again.")

    # Execute AI move immediately (sub-millisecond)
    ai_pos = get_ai_move(board, diff, ai, human)
    if ai_pos is not None:
        board[ai_pos] = ai
        ai_winner = check_winner(board)
        if ai_winner == ai:
            state["game_over"] = True
            state["result"] = ai
            state["winning_cells"] = get_winning_cells(board)
            state["x_score" if ai == X else "o_score"] += 1
            return display(state, f"🤖 **AI ({ai}) wins!** Click **New Board** to try again.")

        if is_board_full(board):
            state["game_over"] = True
            state["result"] = "Draw"
            state["draws"] += 1
            return display(state, "🤝 **It's a Draw!** Click **New Board** to play again.")

        return display(state, f"🤖 AI placed **{ai}** at square **{ai_pos + 1}**.\n\n👉 **Your turn!**")

    # Fallback if board became full
    state["game_over"] = True
    state["result"] = "Draw"
    state["draws"] += 1
    return display(state, "🤝 **It's a Draw!** Click **New Board** to play again.")


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
    transition: transform 0.15s ease !important;
}

.board-btn:hover {
    transform: scale(1.02);
}
"""

# ============================================================
# GRADIO INTERFACE
# ============================================================

with gr.Blocks(title="Tic-Tac-Toe", css=css) as app:

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

    game_state = gr.State(create_state("PvE", "Hard", X))

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
                "🎮 Start / Restart",
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
                        button = gr.Button(" ", elem_classes=["board-btn"])
                        board_buttons.append(button)

            status = gr.Markdown(
                "🤖 **Player vs AI**\n\n"
                "You are ❌ **X** | AI is ⭕ **O** (Hard)\n\n"
                "👉 **Your turn! Click any square to move.**"
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

    # Controls
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

    # Clean function factory for board clicks (no separate gr.State allocations)
    def create_handler(pos):
        return lambda s: player_move(pos, s)

    for pos, btn in enumerate(board_buttons):
        btn.click(
            fn=create_handler(pos),
            inputs=[game_state],
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
