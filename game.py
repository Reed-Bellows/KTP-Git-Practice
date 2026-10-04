"""A two-player checkers game for the terminal."""

from __future__ import annotations

from dataclasses import dataclass


BOARD_SIZE = 8
RED = "r"
BLACK = "b"
PLAYERS = (RED, BLACK)
PLAYER_NAMES = {RED: "Red", BLACK: "Black"}


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

	def display(self):
		print("\n    a   b   c   d   e   f   g   h")
		print("  +---+---+---+---+---+---+---+---+")
		for row in range(BOARD_SIZE):
			cells = [self.board[row][col] or ("." if (row + col) % 2 else " ") for col in range(BOARD_SIZE)]
			print(f"{8 - row} | " + " | ".join(cells) + f" | {8 - row}")
			print("  +---+---+---+---+---+---+---+---+")
		print("    a   b   c   d   e   f   g   h")
		print("Pieces: r/b are men; R/B are kings.\n")


def play():
	game = CheckersGame()
	print("Two-player Checkers. Enter moves like 'b6 a5'; type 'quit' to stop.")
	print("Captures are mandatory. Complete multiple jumps with the same piece.")

	while True:
		game.display()
		winner = game.winner()
		if winner:
			print(f"{PLAYER_NAMES[winner]} wins!")
			return

		player = PLAYER_NAMES[game.current_player]
		if game.forced_piece:
			print("You must continue jumping with the selected piece.")
		try:
			entered_move = input(f"{player} to move: ").strip()
		except (EOFError, KeyboardInterrupt):
			print("\nGame ended.")
			return
		if entered_move.lower() in {"quit", "exit"}:
			print("Game ended.")
			return

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


if __name__ == "__main__":
	play()
