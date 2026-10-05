"""A two-player checkers game for the terminal."""

from __future__ import annotations

from dataclasses import dataclass


BOARD_SIZE = 8
RED = "r"
BLACK = "b"
PLAYER_NAMES = {RED: "Red", BLACK: "Black"}
PIECE_SYMBOLS = {RED: "🔴", BLACK: "⚫"}
COLUMNS = "abcdefgh"


@dataclass(frozen=True)
class Move:
	start: tuple[int, int]
	end: tuple[int, int]
	captured: tuple[int, int] | None = None

	def __str__(self):
		return f"{square_to_text(self.start)} {square_to_text(self.end)}"


def opponent(player):
	return BLACK if player == RED else RED


def owner(piece):
	return piece.lower() if piece else None


def in_bounds(row, col):
	return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def parse_square(text):
	text = text.strip().lower()
	if len(text) != 2 or text[0] not in COLUMNS or text[1] not in "12345678":
		raise ValueError(f"'{text}' is not a square. Use a square such as b6.")
	return BOARD_SIZE - int(text[1]), COLUMNS.index(text[0])


def square_to_text(square):
	row, col = square
	return f"{COLUMNS[col]}{BOARD_SIZE - row}"


class CheckersGame:
	def __init__(self):
		self.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
		for row in range(BOARD_SIZE):
			for col in range(BOARD_SIZE):
				if (row + col) % 2 == 1:
					if row < 3:
						self.board[row][col] = RED
					elif row >= BOARD_SIZE - 3:
						self.board[row][col] = BLACK
		self.current_player = RED
		self.forced_piece = None

	def piece_at(self, square):
		return self.board[square[0]][square[1]]

	@staticmethod
	def row_directions(piece):
		if piece.isupper():
			return (-1, 1)
		return (1,) if piece == RED else (-1,)

	def moves_for_piece(self, row, col):
		"""Return (captures, steps) available to the piece on this square."""
		piece = self.board[row][col]
		captures, steps = [], []
		for row_step in self.row_directions(piece):
			for col_step in (-1, 1):
				mid_row, mid_col = row + row_step, col + col_step
				if not in_bounds(mid_row, mid_col):
					continue
				middle = self.board[mid_row][mid_col]
				if middle is None:
					steps.append(Move((row, col), (mid_row, mid_col)))
					continue
				land_row, land_col = row + 2 * row_step, col + 2 * col_step
				if (
					owner(middle) != owner(piece)
					and in_bounds(land_row, land_col)
					and self.board[land_row][land_col] is None
				):
					captures.append(Move((row, col), (land_row, land_col), (mid_row, mid_col)))
		return captures, steps

	def legal_moves(self):
		"""All legal moves for the current player. Captures are mandatory."""
		if self.forced_piece is not None:
			captures, _ = self.moves_for_piece(*self.forced_piece)
			return captures

		all_captures, all_steps = [], []
		for row in range(BOARD_SIZE):
			for col in range(BOARD_SIZE):
				if owner(self.board[row][col]) == self.current_player:
					captures, steps = self.moves_for_piece(row, col)
					all_captures.extend(captures)
					all_steps.extend(steps)
		return all_captures or all_steps

	def apply_move(self, move):
		piece = self.piece_at(move.start)
		self.board[move.start[0]][move.start[1]] = None
		self.board[move.end[0]][move.end[1]] = piece
		if move.captured:
			self.board[move.captured[0]][move.captured[1]] = None

		promotion_row = BOARD_SIZE - 1 if piece == RED else 0
		promoted = piece.islower() and move.end[0] == promotion_row
		if promoted:
			self.board[move.end[0]][move.end[1]] = piece.upper()

		# A capture that doesn't crown the piece must continue if another jump is available.
		if move.captured and not promoted and self.moves_for_piece(*move.end)[0]:
			self.forced_piece = move.end
			return

		self.forced_piece = None
		self.current_player = opponent(self.current_player)

	def winner(self):
		"""The current player loses when they have no pieces or no legal moves."""
		if not self.legal_moves():
			return opponent(self.current_player)
		return None

	def count_pieces(self, player):
		return sum(owner(piece) == player for row in self.board for piece in row)

	def display(self):
		header = "     " + "    ".join(COLUMNS)
		divider = "   +" + "----+" * BOARD_SIZE
		print("\n" + header)
		print(divider)
		for row in range(BOARD_SIZE):
			cells = []
			for col in range(BOARD_SIZE):
				piece = self.board[row][col]
				if piece is None:
					cells.append(" ·  " if (row + col) % 2 == 1 else "    ")
				else:
					king_mark = "K" if piece.isupper() else " "
					cells.append(f" {PIECE_SYMBOLS[owner(piece)]}{king_mark}")
			rank = BOARD_SIZE - row
			print(f" {rank} |" + "|".join(cells) + f"| {rank}")
			print(divider)
		print(header)
		print(
			f"\n{PIECE_SYMBOLS[RED]} Red: {self.count_pieces(RED)}   "
			f"{PIECE_SYMBOLS[BLACK]} Black: {self.count_pieces(BLACK)}   "
			"(K = king)\n"
		)


def read_input(prompt):
	try:
		text = input(prompt).strip().lower()
	except (EOFError, KeyboardInterrupt):
		text = "quit"
		print()
	if text in {"quit", "exit", "q"}:
		print("Game ended.")
		raise SystemExit
	return text


def choose_move(game):
	"""Keep asking the current player until they enter a legal move."""
	player = PLAYER_NAMES[game.current_player]
	legal = game.legal_moves()

	while True:
		text = read_input(f"{player} to move: ")
		if text in {"help", "moves", "?"}:
			print("Legal moves: " + ", ".join(str(move) for move in legal))
			continue

		parts = text.replace("-", " ").split()
		try:
			squares = [parse_square(part) for part in parts]
		except ValueError as error:
			print(error)
			continue

		if len(squares) == 1:
			start = squares[0]
			options = [move for move in legal if move.start == start]
			if not options:
				print(explain_bad_start(game, start, legal))
				continue
			if len(options) == 1:
				return options[0]
			targets = ", ".join(square_to_text(move.end) for move in options)
			try:
				end = parse_square(read_input(f"Move {square_to_text(start)} to ({targets}): "))
			except ValueError as error:
				print(error)
				continue
			squares.append(end)

		if len(squares) != 2:
			print("Enter a piece and a destination, such as b6 a5. Type 'moves' for help.")
			continue

		start, end = squares
		move = next((m for m in legal if m.start == start and m.end == end), None)
		if move is None:
			print(explain_bad_start(game, start, legal) or "That piece can't move there.")
			continue
		return move


def explain_bad_start(game, start, legal):
	piece = game.piece_at(start)
	if piece is None:
		return "That square is empty. Pick one of your pieces."
	if owner(piece) != game.current_player:
		return "That's not your piece."
	if game.forced_piece and start != game.forced_piece:
		return f"You must keep jumping with {square_to_text(game.forced_piece)}."
	if not any(move.start == start for move in legal):
		if legal and legal[0].captured:
			return "A capture is available, so you must take it. Type 'moves' to see it."
		return "That piece has no legal moves."
	return None


def play():
	game = CheckersGame()
	print("Two-player Checkers")
	print("Enter moves like 'b6 a5', or type a square to pick a piece first.")
	print("Captures are mandatory. Type 'moves' for hints or 'quit' to stop.")

	while True:
		game.display()
		winner = game.winner()
		if winner:
			print(f"{PLAYER_NAMES[winner]} wins! 🎉")
			return
		if game.forced_piece:
			print(f"Keep jumping with {square_to_text(game.forced_piece)}!")
		game.apply_move(choose_move(game))


if __name__ == "__main__":
	play()
