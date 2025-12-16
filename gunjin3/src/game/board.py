from typing import Optional, List, Tuple
from .piece import Piece, Side, Rank

# Board dimensions
ROWS = 8
COLS = 6
HQ_POSITIONS = {
    Side.FRONT: [(7, 2), (7, 3)], # Front HQ (merged)
    Side.BACK: [(0, 2), (0, 3)]   # Back HQ (merged)
}

class Board:
    def __init__(self):
        # 8x6 grid. None means empty.
        # Coordinates: (row, col). (0,0) is Top-Left (Back side's deep left).
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(COLS)] for _ in range(ROWS)]
        
    def place_piece(self, piece: Piece, row: int, col: int):
        if not (0 <= row < ROWS and 0 <= col < COLS):
            raise ValueError(f"Position ({row}, {col}) is out of bounds")
        self.grid[row][col] = piece

    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        if not (0 <= row < ROWS and 0 <= col < COLS):
            return None
        return self.grid[row][col]

    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        piece = self.get_piece(*from_pos)
        if not piece:
            raise ValueError("No piece at starting position")
        
        # Simple move (no validation here, just state update)
        self.grid[to_pos[0]][to_pos[1]] = piece
        self.grid[from_pos[0]][from_pos[1]] = None

    def remove_piece(self, row: int, col: int):
        self.grid[row][col] = None

    def is_hq(self, row: int, col: int) -> bool:
        # Check if a cell is part of an HQ
        for side in Side:
            if (row, col) in HQ_POSITIONS[side]:
                return True
        return False

    def get_hq_owner(self, row: int, col: int) -> Optional[Side]:
        for side, positions in HQ_POSITIONS.items():
            if (row, col) in positions:
                return side
        return None
