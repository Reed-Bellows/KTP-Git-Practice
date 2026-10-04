"""A two-player checkers game for the terminal."""

from __future__ import annotations

from dataclasses import dataclass


RESET = "\033[0m"
RED_TEXT = "\033[1;31m"
BLACK_TEXT = "\033[30m"
LIGHT_BG = "\033[46m"
DARK_BG = "\033[44m"

BOARD_SIZE = 8
RED = "r"
BLACK = "b"
PLAYERS = (RED, BLACK)
PLAYER_NAMES = {RED: "Red", BLACK: "Black"}
PIECE_SYMBOLS = {
	RED: "●",
	BLACK: "●",
	RED.upper(): "●",
	BLACK.upper(): "●",
}
PIECE_COLORS = {
	RED: RED_TEXT,
	BLACK: BLACK_TEXT,
	RED.upper(): RED_TEXT,
	BLACK.upper(): BLACK_TEXT,
}


@dataclass(frozen=True)
class Move:
	start: tuple[int, int]
	end: tuple[int, int]
	captured: tuple[int, int] | None = None


class CheckersGame:
	def __init__(self):
		self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
		for row in range(3):
			for col in range(BOARD_SIZE):
				if (row + col) % 2 == 1:
					self.board[row][col] = RED
		for row in range(5, BOARD_SIZE):
			for col in range(BOARD_SIZE):
				if (row + col) % 2 == 1:
					self.board[row][col] = BLACK
		self.current_player = RED
		self.forced_piece = None

	@staticmethod
	def owner(piece):
		return piece.lower() if piece else None

	def directions(self, piece):
		if piece.isupper():
			return (-1, 1)
		return (1,) if piece == RED else (-1,)

	def moves_for_piece(self, row, col, captures_only=False):
		piece = self.board[row][col]
		moves = []
		for row_step in self.directions(piece):
			for col_step in (-1, 1):
				next_row, next_col = row + row_step, col + col_step
				if not self.in_bounds(next_row, next_col):
					continue
				if self.board[next_row][next_col] is None and not captures_only:
					moves.append(Move((row, col), (next_row, next_col)))
					continue

				jump_row, jump_col = row + 2 * row_step, col + 2 * col_step
				if (
					self.in_bounds(jump_row, jump_col)
					and self.board[next_row][next_col] is not None
					and self.owner(self.board[next_row][next_col]) != self.current_player
					and self.board[jump_row][jump_col] is None
				):
					moves.append(Move((row, col), (jump_row, jump_col), (next_row, next_col)))
		return moves

	def legal_moves(self):
		if self.forced_piece is not None:
			row, col = self.forced_piece
			return self.moves_for_piece(row, col, captures_only=True)

		captures = []
		steps = []
		for row in range(BOARD_SIZE):
			for col in range(BOARD_SIZE):
				piece = self.board[row][col]
				if self.owner(piece) == self.current_player:
					piece_moves = self.moves_for_piece(row, col)
					captures.extend(move for move in piece_moves if move.captured)
					steps.extend(move for move in piece_moves if not move.captured)
		return captures or steps

	def apply_move(self, move):
		piece = self.board[move.start[0]][move.start[1]]
		self.board[move.start[0]][move.start[1]] = None
		self.board[move.end[0]][move.end[1]] = piece
		if move.captured:
			self.board[move.captured[0]][move.captured[1]] = None

		promotion_row = 0 if self.current_player == BLACK else BOARD_SIZE - 1
		promoted = piece.islower() and move.end[0] == promotion_row
		if promoted:
			self.board[move.end[0]][move.end[1]] = piece.upper()

		if move.captured and not promoted:
			follow_up_captures = self.moves_for_piece(*move.end, captures_only=True)
			if follow_up_captures:
				self.forced_piece = move.end
				return

		self.forced_piece = None
		self.current_player = BLACK if self.current_player == RED else RED

	def winner(self):
		opponent = BLACK if self.current_player == RED else RED
		has_pieces = any(self.owner(piece) == self.current_player for row in self.board for piece in row)
		if not has_pieces or not self.legal_moves():
			return opponent
		return None

	@staticmethod
	def in_bounds(row, col):
		return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

	@staticmethod
	def parse_square(text):
		text = text.lower()
		if len(text) != 2 or text[0] not in "abcdefgh" or text[1] not in "12345678":
			raise ValueError("Use a square such as b6.")
		return 8 - int(text[1]), ord(text[0]) - ord("a")

	@staticmethod
	def parse_move(text):
		parts = text.lower().replace("-", " ").split()
		if len(parts) != 2:
			raise ValueError("Enter a starting square and destination, such as b6 a5.")
		return Move(CheckersGame.parse_square(parts[0]), CheckersGame.parse_square(parts[1]))

	@staticmethod
	def square_to_text(square):
		row, col = square
		return f"{chr(ord('a') + col)}{8 - row}"

	def display(self):
		print("\n      a   b   c   d   e   f   g   h")
		print("    +---+---+---+---+---+---+---+---+")
		for row in range(BOARD_SIZE):
			cells = []
			for col in range(BOARD_SIZE):
				piece = self.board[row][col]
				bg = LIGHT_BG if (row + col) % 2 == 0 else DARK_BG
				if piece is None:
					cells.append(f"{bg}   {RESET}")
				else:
					cells.append(f"{bg}{PIECE_COLORS.get(piece, RED_TEXT)}{PIECE_SYMBOLS.get(piece, piece)}{RESET}")
			print(f" {8 - row} | " + " | ".join(cells) + f" | {8 - row}")
			print("    +---+---+---+---+---+---+---+---+")
		print("      a   b   c   d   e   f   g   h")
		print("Pieces: red and black circles are color-coded.\n")


def prompt_for_square(label):
	while True:
		try:
			text = input(f"{label}: ").strip()
		except (EOFError, KeyboardInterrupt):
			print("\nGame ended.")
			raise SystemExit
		if text.lower() in {"quit", "exit"}:
			print("Game ended.")
			raise SystemExit
		try:
			return CheckersGame.parse_square(text)
		except ValueError as error:
			print(error)


def play():
	game = CheckersGame()
	print("Two-player Checkers. Use the keyboard to select a piece and a destination.")
	print("Terminal click support is not available; type coordinates like 'b6 a5'.")
	print("Captures are mandatory. Complete multiple jumps with the same piece.")
	while True:
		game.display()
		winner = game.winner()
		if winner:
			print(f"{PLAYER_NAMES[winner]} wins!")
			return

		player = PLAYER_NAMES[game.current_player]
		if game.forced_piece:
			print(f"You must continue jumping with {CheckersGame.square_to_text(game.forced_piece)}.")

		while True:
			try:
				entered_move = input(f"{player} to move: ").strip()
			except (EOFError, KeyboardInterrupt):
				print("\nGame ended.")
				return
			if entered_move.lower() in {"quit", "exit"}:
				print("Game ended.")
				return

			if " " in entered_move:
				try:
					requested_move = game.parse_move(entered_move)
				except ValueError as error:
					print(error)
					continue
				legal_move = next(
					(
						move
						for move in game.legal_moves()
						if move.start == requested_move.start and move.end == requested_move.end
					),
					None,
				)
				if legal_move is None:
					print("That move is not legal. Check the board and try again.")
					continue
				game.apply_move(legal_move)
				break

			try:
				start = CheckersGame.parse_square(entered_move)
			except ValueError as error:
				print(error)
				continue
			piece = game.board[start[0]][start[1]]
			if piece is None:
				print("That square is empty. Pick one of your pieces.")
				continue
			if game.owner(piece) != game.current_player:
				print("Pick one of your own pieces.")
				continue
			start_moves = [move for move in game.legal_moves() if move.start == start]
			if not start_moves:
				print("That piece has no legal moves.")
				continue
			if game.forced_piece and start != game.forced_piece:
				print(f"You must keep using {CheckersGame.square_to_text(game.forced_piece)}.")
				continue
			break
		if " " not in entered_move:
			end = prompt_for_square(f"{player} choose destination for {CheckersGame.square_to_text(start)}")
			legal_move = next((move for move in start_moves if move.end == end), None)
			if legal_move is None:
				print("That destination is not legal for that piece. Try again.")
				continue
			game.apply_move(legal_move)
			break


if __name__ == "__main__":
	play()
