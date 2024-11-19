from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Store game state in memory
games = {}

def create_board():
    return [[" " for _ in range(7)] for _ in range(6)]

def is_valid_move(board, col):
    return board[0][col] == " "

def make_move(board, col, player):
    for row in reversed(board):
        if row[col] == " ":
            row[col] = player
            return True
    return False

def check_winner(board, player):
    # Horizontal, vertical, diagonal checks
    for row in range(6):
        for col in range(7):
            if (
                col + 3 < 7 and all(board[row][c] == player for c in range(col, col + 4)) or
                row + 3 < 6 and all(board[r][col] == player for r in range(row, row + 4)) or
                row + 3 < 6 and col + 3 < 7 and all(board[row + i][col + i] == player for i in range(4)) or
                row + 3 < 6 and col - 3 >= 0 and all(board[row + i][col - i] == player for i in range(4))
            ):
                return True
    return False

@app.route("/")
def home():
    return "Welcome to Connect 4! Create a game by visiting /create"

@app.route("/create")
def create_game():
    game_id = request.args.get("game_id", "game123")
    games[game_id] = {
        "board": create_board(),
        "players": [],
        "current_turn": "X"
    }
    return f"Game created! Share this link with a friend: /game/{game_id}"

@app.route("/game/<game_id>")
def game(game_id):
    if game_id not in games:
        return "Game not found!"
    return render_template("game.html", game_id=game_id)

@socketio.on("join")
def on_join(data):
    game_id = data["game_id"]
    player = data["player"]
    join_room(game_id)

    if len(games[game_id]["players"]) < 2:
        games[game_id]["players"].append(player)
        emit("player_joined", {"player": player, "players": games[game_id]["players"]}, room=game_id)
    else:
        emit("error", {"message": "Game is full."}, to=request.sid)

@socketio.on("move")
def on_move(data):
    game_id = data["game_id"]
    col = data["col"]
    player = data["player"]

    game = games[game_id]
    if player != game["current_turn"]:
        emit("error", {"message": "Not your turn."}, to=request.sid)
        return

    if is_valid_move(game["board"], col):
        make_move(game["board"], col, player)
        if check_winner(game["board"], player):
            emit("game_over", {"winner": player}, room=game_id)
        else:
            game["current_turn"] = "O" if player == "X" else "X"
            emit("update", {"board": game["board"], "current_turn": game["current_turn"]}, room=game_id)
    else:
        emit("error", {"message": "Invalid move."}, to=request.sid)

if __name__ == "__main__":
    socketio.run(app, debug=True)
