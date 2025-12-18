from typing import Tuple, Optional
from .piece import Piece, Rank, Side
from .board import Board, ROWS, COLS, HQ_POSITIONS

class MoveValidator:
    def __init__(self, board: Board):
        self.board = board

    def is_valid_move(self, piece: Piece, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        # HQ Targeting Leniency
        # If target is HQ, allow move if valid to ANY cell of that HQ.
        potential_targets = [to_pos]
        if self.board.is_hq(*to_pos):
            hq_owner = self.board.get_hq_owner(*to_pos)
            if hq_owner:
                potential_targets = HQ_POSITIONS[hq_owner]
        
        # HQ Departure Leniency
        # If starting from HQ, treat as starting from ANY cell of that HQ.
        potential_starts = [from_pos]
        if self.board.is_hq(*from_pos):
            hq_owner = self.board.get_hq_owner(*from_pos)
            if hq_owner:
                potential_starts = HQ_POSITIONS[hq_owner]

        for start in potential_starts:
            for target in potential_targets:
                if self._check_single_move(piece, start, target):
                    return True
        return False

    def _check_single_move(self, piece: Piece, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
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

        # HQ Entry Restriction (REMOVED: All pieces can enter, but only Officers can win)
        # if self.board.is_hq(tr, tc):
        #     hq_owner = self.board.get_hq_owner(tr, tc)
        #     if hq_owner and hq_owner != piece.side:
        #         # Entering enemy HQ: Only Major (10) to Marshal (15) allowed
        #         if not (Rank.MAJOR.value <= piece.rank.value <= Rank.MARSHAL.value):
        #             return False

        # Direction Logic
        dr = tr - fr
        dc = tc - fc
        abs_dr = abs(dr)
        abs_dc = abs(dc)
        
        forward_dir = -1 if piece.side == Side.FRONT else 1
        is_forward = (dr == forward_dir) or (dr == forward_dir * 2)
        is_backward = (dr == -forward_dir) or (dr == -forward_dir * 2) # Plane can fly back
        
        # River Crossing Check
        # River is between Row 2 and Row 3.
        crossing_river = (fr <= 2 and tr >= 3) or (fr >= 3 and tr <= 2)
        is_bridge_col = (fc == 1 or fc == 6) and (tc == 1 or tc == 6) # Must stay on bridge col if crossing?
        # Actually, if crossing river, you must be at Col 1 or 6 UNLESS you are Plane.
        # Or if you are Tank/Cavalry jumping?
        # RULES: "工兵は水を通過できないが、橋は通過できる" -> Must use bridge.
        # "飛行機...水を無視して" -> Can cross anywhere.
        
        if crossing_river:
            if piece.rank == Rank.PLANE:
                pass # Allowed anywhere
            else:
                # Must be at bridge column (1 or 6) AND destination must be bridge column?
                # Usually bridge is straight.
                if not (fc == 1 or fc == 6):
                    return False # Starting from non-bridge col
                if not (tc == 1 or tc == 6):
                    return False # Landing on non-bridge col (unless diagonal? No diagonal)
                if fc != tc:
                    return False # Must cross straight

        # Specific Piece Movement
        
        if piece.rank in [Rank.MINE, Rank.FLAG]:
            return False

        # Standard (Infantry, Officers, Spy): 1 step orthogonal
        if piece.rank in [Rank.INFANTRY, Rank.SPY] or (Rank.SEC_LT.value <= piece.rank.value <= Rank.MARSHAL.value):
            return (abs_dr + abs_dc == 1)

        # Tank / Cavalry
        if piece.rank in [Rank.TANK, Rank.CAVALRY]:
            # Forward: 1 or 2 steps
            if dc == 0 and dr == forward_dir * 2:
                # 2 steps forward
                # Check obstruction
                mid_r = fr + forward_dir
                if self.board.get_piece(mid_r, fc) is not None:
                    return False # Blocked
                return True
            
            # 1 step orthogonal (Forward/Back/Left/Right)
            return (abs_dr + abs_dc == 1)

        # Engineer (Rook-like)
        if piece.rank == Rank.ENGINEER:
            if dr != 0 and dc != 0:
                return False # No diagonal
            
            # Check path clear
            step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
            step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
            
            curr_r, curr_c = fr + step_r, fc + step_c
            while (curr_r, curr_c) != (tr, tc):
                if self.board.get_piece(curr_r, curr_c) is not None:
                    return False # Blocked
                
                # Check River crossing for Engineer
                # If passing through river boundary (Row 2<->3)
                prev_r = curr_r - step_r
                if (prev_r <= 2 and curr_r >= 3) or (prev_r >= 3 and curr_r <= 2):
                    if not (curr_c == 1 or curr_c == 6):
                        return False # Cannot cross water
                
                curr_r += step_r
                curr_c += step_c
                
            # Check River crossing for final step if applicable
            # (Handled by loop if distance > 1, but if distance is 1, loop doesn't run)
            if crossing_river and not (fc == 1 or fc == 6):
                return False

            return True

        # Plane
        if piece.rank == Rank.PLANE:
            # Forward/Back: Any distance
            # Left/Right: 1 step
            
            if dc == 0: # Vertical move (Forward or Back)
                return True # Can jump, can cross water
            
            if dr == 0: # Horizontal move
                return abs_dc == 1
            
            return False # No diagonal

        return False

class CombatEngine:
    def resolve_combat(self, attacker: Piece, defender: Piece, attacker_pos: Tuple[int, int], defender_pos: Tuple[int, int], board: Board) -> int:
        """
        Returns:
         1: Attacker wins
        -1: Defender wins
         0: Draw (both die)
        """
        
        # Resolve Defender if Flag
        effective_defender_rank = defender.rank
        
        if defender.rank == Rank.FLAG:
            # Determine support
            behind_pos = None
            if defender.side == Side.FRONT:
                behind_pos = (defender_pos[0] + 1, defender_pos[1])
            else:
                behind_pos = (defender_pos[0] - 1, defender_pos[1])
            
            support_piece = board.get_piece(*behind_pos)
            
            if support_piece and support_piece.side == defender.side:
                effective_defender_rank = support_piece.rank
            else:
                # No support or enemy behind (weird) -> Weakest
                # Flag loses to everything if unsupported?
                # RULES: "軍旗の後ろが敵駒・空白・最後列の場合、全ての駒に負ける"
                return 1 # Attacker wins
        
        # Special Matchups Table
        
        # Attacker: Plane
        if attacker.rank == Rank.PLANE:
            if effective_defender_rank in [Rank.MARSHAL, Rank.GENERAL, Rank.LT_GEN]:
                return -1 # Plane loses to Generals
            return 1 # Plane wins against everything else (including Mine, Tank, etc)
            
        # Defender: Plane
        if effective_defender_rank == Rank.PLANE:
            if attacker.rank in [Rank.MARSHAL, Rank.GENERAL, Rank.LT_GEN]:
                return 1 # Generals kill Plane
            return -1 # Plane kills everything else
            
        # Defender: Mine (or Flag mimicking Mine)
        if effective_defender_rank == Rank.MINE:
            if attacker.rank == Rank.ENGINEER:
                return 1 # Engineer disarms Mine
            if attacker.rank == Rank.PLANE:
                return 1 # Plane destroys Mine (Handled above actually)
            return 0 # Draw (Both die) - RULES: "地雷...その他の駒とは相討ち"
            
        # Attacker: Tank
        if attacker.rank == Rank.TANK:
            if effective_defender_rank in [Rank.MARSHAL, Rank.GENERAL, Rank.LT_GEN, Rank.PLANE, Rank.ENGINEER, Rank.MINE]:
                return -1 # Tank loses to Generals, Plane, Engineer, Mine(Draw? No, Mine is handled above)
                # Wait, Tank vs Mine?
                # RULES Table: Tank vs Mine -> = (Draw)
                # My Mine logic above returns 0 (Draw). Correct.
                # Tank vs Engineer -> Tank loses?
                # RULES Table: Tank vs Engineer -> X (Tank loses). Correct.
            return 1 # Tank wins against others
            
        # Defender: Tank
        if effective_defender_rank == Rank.TANK:
            if attacker.rank in [Rank.MARSHAL, Rank.GENERAL, Rank.LT_GEN, Rank.PLANE, Rank.ENGINEER, Rank.MINE]:
                # Attacker wins?
                # Generals vs Tank -> Win
                # Plane vs Tank -> Win
                # Engineer vs Tank -> Win (RULES: Engineer vs Tank -> O)
                # Mine vs Tank -> Draw (Handled)
                return 1
            return -1 # Tank wins
            
        # Attacker: Spy
        if attacker.rank == Rank.SPY:
            if effective_defender_rank == Rank.MARSHAL:
                return 1
            if effective_defender_rank == Rank.SPY:
                return 0
            return -1
            
        # Defender: Spy
        if effective_defender_rank == Rank.SPY:
            if attacker.rank == Rank.MARSHAL:
                return -1 # Marshal dies to Spy? No, Spy vs Marshal -> Spy wins. Marshal vs Spy -> Marshal loses.
                # Wait, RULES Table:
                # Attacker(Marshal) vs Defender(Spy) -> O (Marshal Wins)
                # Attacker(Spy) vs Defender(Marshal) -> O (Spy Wins)
                # So Spy only wins if ATTACKING?
                # RULES text: "スパイ...大将にのみ勝利"
                # Table:
                # Spy (row) vs Marshal (col) -> O
                # Marshal (row) vs Spy (col) -> O
                # Wait, Marshal vs Spy is O (Win). So Marshal kills Spy.
                # Spy vs Marshal is O (Win). So Spy kills Marshal.
                # So whoever attacks wins?
                # Let's check standard Gunjin Shogi. Usually Spy kills Marshal always.
                # But Table says: Marshal vs Spy -> O.
                # This means Marshal attacks Spy -> Marshal wins.
                # Spy attacks Marshal -> Spy wins.
                # Interesting.
                pass # Fall through to rank comparison? No, Spy is rank 1. Marshal is 15.
                # If Marshal attacks Spy: 15 > 1 -> Win. Correct.
                # If Spy attacks Marshal: Special case needed.
        
        if attacker.rank == Rank.SPY and effective_defender_rank == Rank.MARSHAL:
            return 1
            
        # Standard Rank Comparison
        if attacker.rank.value > effective_defender_rank.value:
            return 1
        elif attacker.rank.value < effective_defender_rank.value:
            return -1
        else:
            return 0

