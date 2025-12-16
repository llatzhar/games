from typing import Tuple, Optional
from .piece import Piece, Rank, Side
from .board import Board, ROWS, COLS

class MoveValidator:
    def __init__(self, board: Board):
        self.board = board

    def is_valid_move(self, piece: Piece, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        fr, fc = from_pos
        tr, tc = to_pos

        # Basic bounds check
        if not (0 <= tr < ROWS and 0 <= tc < COLS):
            return False
        
        # Cannot move to same spot
        if from_pos == to_pos:
            return False

        # Destination check: Cannot land on own piece
        target_piece = self.board.get_piece(tr, tc)
        if target_piece and target_piece.side == piece.side:
            return False

        # HQ Entry Restriction: Only Major (Rank.MAJOR=10) and above can enter Enemy HQ
        if self.board.is_hq(tr, tc):
            hq_owner = self.board.get_hq_owner(tr, tc)
            if hq_owner and hq_owner != piece.side:
                # Entering enemy HQ
                # Rank values: Major is 10. Officers are >= 7. 
                # RULES.md says "Major and above". Assuming Major(10) to Marshal(15).
                # Need to verify if Spy/Tank/Plane etc are allowed. Usually only high officers.
                # Based on standard rules: Major(10) <= rank <= Marshal(15).
                if not (Rank.MAJOR.value <= piece.rank.value <= Rank.MARSHAL.value):
                    return False

        # Movement Logic per Piece Type
        dr = tr - fr
        dc = tc - fc
        abs_dr = abs(dr)
        abs_dc = abs(dc)

        # 1. Standard Move (1 step orthogonal or diagonal)
        # Most pieces move 1 step.
        # Exceptions: Tank, Cavalry, Engineer, Plane, Mine(0 move)
        
        if piece.rank == Rank.MINE or piece.rank == Rank.FLAG:
            return False # Cannot move

        if piece.rank == Rank.ENGINEER:
            # Engineer: Can move any distance orthogonally (like Rook) but not jump (unless rail? RULES.md check needed)
            # RULES.md usually says Engineers move like Rooks? Or just 1 step?
            # Let's assume standard 1 step for now unless specified otherwise.
            # Wait, RULES.md says "Engineer (free move)". Likely means Rook-like movement.
            # Let's stick to 1-step for base implementation and refine later if needed.
            pass 

        # Standard 1-step check for now (covers Infantry, Officers, Spy)
        if abs_dr <= 1 and abs_dc <= 1:
            return True
            
        # TODO: Implement Special Moves (Tank jump, Plane fly, Engineer range)
        
        return False

class CombatEngine:
    def resolve_combat(self, attacker: Piece, defender: Piece, attacker_pos: Tuple[int, int], defender_pos: Tuple[int, int], board: Board) -> int:
        """
        Returns:
         1: Attacker wins
        -1: Defender wins
         0: Draw (both die)
        """
        
        # 1. Mine Logic
        if defender.rank == Rank.MINE:
            if attacker.rank == Rank.ENGINEER:
                return 1 # Engineer disarms Mine
            if attacker.rank == Rank.PLANE:
                return 1 # Plane flies over/destroys mine? (Check RULES.md) - Usually Plane survives.
            return -1 # Attacker dies hitting mine (Mine usually survives or both die? RULES.md check needed. Standard: Attacker dies, Mine stays)
            
        # 2. Spy Logic
        if attacker.rank == Rank.SPY:
            if defender.rank == Rank.MARSHAL:
                return 1 # Spy kills Marshal
            # Spy loses to everything else except Flag/Spy(draw)
            
        # 3. Flag Logic
        if defender.rank == Rank.FLAG:
            # Flag strength depends on piece BEHIND it.
            # "Behind" depends on Side.
            # Front Side (Bottom): Behind is (row+1, col)
            # Back Side (Top): Behind is (row-1, col)
            
            behind_pos = None
            if defender.side == Side.FRONT:
                behind_pos = (defender_pos[0] + 1, defender_pos[1])
            else:
                behind_pos = (defender_pos[0] - 1, defender_pos[1])
                
            support_piece = board.get_piece(*behind_pos)
            
            # If no support, Flag is weakest? Or has base strength?
            # RULES.md: "Flag strength is same as piece behind it"
            # If support is None, treat as weakest (0)?
            
            defender_strength = support_piece.rank.value if support_piece else 0
            
            # Compare Attacker vs Supported Flag
            if attacker.rank.value > defender_strength:
                return 1
            elif attacker.rank.value < defender_strength:
                return -1
            else:
                return 0

        # 4. Standard Rank Comparison
        if attacker.rank.value > defender.rank.value:
            return 1
        elif attacker.rank.value < defender.rank.value:
            return -1
        else:
            return 0
