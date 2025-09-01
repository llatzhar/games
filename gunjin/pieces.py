"""
駒クラス定義
"""

import random
from constants import *

class Piece:
    """駒クラス"""
    
    def __init__(self, piece_type, player, x=0, y=0):
        self.piece_type = piece_type
        self.player = player
        self.x = x
        self.y = y
        self.revealed = False
        self.alive = True
        self.is_hidden = False
        
    def get_name(self):
        """駒の名前を取得"""
        return PIECE_NAMES.get(self.piece_type, "不明")
    
    def get_display_name(self):
        """表示用の駒の名前を取得"""
        if hasattr(self, 'is_hidden') and self.is_hidden:
            return "?"
        return PIECE_NAMES.get(self.piece_type, "?")
    
    def get_position(self):
        """駒の現在位置を取得"""
        return (self.x, self.y)
    
    def can_move(self):
        """駒が移動可能かチェック"""
        if not self.alive:
            return False
        # 隠蔽フラグは移動可能性には影響しない（相手の駒も移動できる）
        # 隠蔽フラグは表示とプレイヤー操作のみに影響
        return self.piece_type not in IMMOVABLE_PIECES
    
    def get_strength(self):
        """駒の強さを取得（小さいほど強い）"""
        return self.piece_type
    
    def can_defeat(self, other_piece):
        """他の駒に勝てるかチェック（READMEの勝敗表に基づく）"""
        if not isinstance(other_piece, Piece):
            return False
            
        my_type = self.piece_type
        other_type = other_piece.piece_type
        
        # 勝敗表（○=True, ×=False, ＝=None）
        battle_table = {
            PIECE_GENERAL: {
                PIECE_GENERAL: None, PIECE_LT_GENERAL: True, PIECE_MAJ_GENERAL: True,
                PIECE_COLONEL: True, PIECE_LT_COLONEL: True, PIECE_MAJOR: True,
                PIECE_CAPTAIN: True, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: True, PIECE_TANK: True, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: False, PIECE_MINE: None
            },
            PIECE_LT_GENERAL: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: None, PIECE_MAJ_GENERAL: True,
                PIECE_COLONEL: True, PIECE_LT_COLONEL: True, PIECE_MAJOR: True,
                PIECE_CAPTAIN: True, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: True, PIECE_TANK: True, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_MAJ_GENERAL: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: None,
                PIECE_COLONEL: True, PIECE_LT_COLONEL: True, PIECE_MAJOR: True,
                PIECE_CAPTAIN: True, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: True, PIECE_TANK: True, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_COLONEL: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: None, PIECE_LT_COLONEL: True, PIECE_MAJOR: True,
                PIECE_CAPTAIN: True, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: False, PIECE_TANK: False, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_LT_COLONEL: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: False, PIECE_LT_COLONEL: None, PIECE_MAJOR: True,
                PIECE_CAPTAIN: True, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: False, PIECE_TANK: False, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_MAJOR: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: False, PIECE_LT_COLONEL: False, PIECE_MAJOR: None,
                PIECE_CAPTAIN: True, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: False, PIECE_TANK: False, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_CAPTAIN: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: False, PIECE_LT_COLONEL: False, PIECE_MAJOR: False,
                PIECE_CAPTAIN: None, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: False, PIECE_TANK: False, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_LT: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: False, PIECE_LT_COLONEL: False, PIECE_MAJOR: False,
                PIECE_CAPTAIN: False, PIECE_LT: None, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: False, PIECE_TANK: False, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_2ND_LT: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: False, PIECE_LT_COLONEL: False, PIECE_MAJOR: False,
                PIECE_CAPTAIN: False, PIECE_LT: False, PIECE_2ND_LT: None,
                PIECE_AIRCRAFT: False, PIECE_TANK: False, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_AIRCRAFT: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: True, PIECE_LT_COLONEL: True, PIECE_MAJOR: True,
                PIECE_CAPTAIN: True, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: None, PIECE_TANK: True, PIECE_CAVALRY: True,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: True
            },
            PIECE_TANK: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: True, PIECE_LT_COLONEL: True, PIECE_MAJOR: True,
                PIECE_CAPTAIN: True, PIECE_LT: True, PIECE_2ND_LT: True,
                PIECE_AIRCRAFT: False, PIECE_TANK: None, PIECE_CAVALRY: True,
                PIECE_ENGINEER: False, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_CAVALRY: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: False, PIECE_LT_COLONEL: False, PIECE_MAJOR: False,
                PIECE_CAPTAIN: False, PIECE_LT: False, PIECE_2ND_LT: False,
                PIECE_AIRCRAFT: False, PIECE_TANK: False, PIECE_CAVALRY: None,
                PIECE_ENGINEER: True, PIECE_SPY: True, PIECE_MINE: None
            },
            PIECE_ENGINEER: {
                PIECE_GENERAL: False, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: False, PIECE_LT_COLONEL: False, PIECE_MAJOR: False,
                PIECE_CAPTAIN: False, PIECE_LT: False, PIECE_2ND_LT: False,
                PIECE_AIRCRAFT: False, PIECE_TANK: True, PIECE_CAVALRY: False,
                PIECE_ENGINEER: None, PIECE_SPY: True, PIECE_MINE: True
            },
            PIECE_SPY: {
                PIECE_GENERAL: True, PIECE_LT_GENERAL: False, PIECE_MAJ_GENERAL: False,
                PIECE_COLONEL: False, PIECE_LT_COLONEL: False, PIECE_MAJOR: False,
                PIECE_CAPTAIN: False, PIECE_LT: False, PIECE_2ND_LT: False,
                PIECE_AIRCRAFT: False, PIECE_TANK: False, PIECE_CAVALRY: False,
                PIECE_ENGINEER: False, PIECE_SPY: None, PIECE_MINE: None
            },
            PIECE_MINE: {
                PIECE_GENERAL: None, PIECE_LT_GENERAL: None, PIECE_MAJ_GENERAL: None,
                PIECE_COLONEL: None, PIECE_LT_COLONEL: None, PIECE_MAJOR: None,
                PIECE_CAPTAIN: None, PIECE_LT: None, PIECE_2ND_LT: None,
                PIECE_AIRCRAFT: False, PIECE_TANK: None, PIECE_CAVALRY: None,
                PIECE_ENGINEER: False, PIECE_SPY: None, PIECE_MINE: None
            }
        }
        
        # 軍旗の特殊処理は別途実装
        if my_type == PIECE_FLAG:
            return self._check_flag_battle(other_piece)
            
        return battle_table.get(my_type, {}).get(other_type, False)
    
    def _check_flag_battle(self, other_piece, board=None, x=None, y=None):
        """軍旗の戦闘判定（後ろの駒の強さに依存）"""
        # 簡略化：現在は常に負けとする（後で実装）
        return False
    
    def battle(self, other_piece):
        """他の駒との戦闘を実行"""
        if not isinstance(other_piece, Piece):
            return "invalid"
            
        if self.player == other_piece.player:
            return "friendly_fire"
        
        print(f"戦闘詳細: {self.get_name()}({self.piece_type}) vs {other_piece.get_name()}({other_piece.piece_type})")
        
        # 戦闘判定
        i_win = self.can_defeat(other_piece)
        they_win = other_piece.can_defeat(self)
        
        print(f"戦闘判定: {self.get_name()}が勝つか={i_win}, {other_piece.get_name()}が勝つか={they_win}")
        
        if i_win is None and they_win is None:
            # 相討ち
            self.alive = False
            other_piece.alive = False
            print("結果: 相討ち（両方None）")
            return "draw"
        elif i_win is None:
            # 自分が相討ち、相手が勝利 → 相討ち
            self.alive = False
            other_piece.alive = False
            print("結果: 相討ち（自分None）")
            return "draw"
        elif they_win is None:
            # 相手が相討ち、自分が勝利 → 相討ち
            self.alive = False
            other_piece.alive = False
            print("結果: 相討ち（相手None）")
            return "draw"
        elif i_win and not they_win:
            # 勝利
            other_piece.alive = False
            print(f"結果: {self.get_name()}の勝利")
            return "win"
        elif not i_win and they_win:
            # 敗北
            self.alive = False
            print(f"結果: {other_piece.get_name()}の勝利")
            return "lose"
        else:
            # 両方がTrueまたは両方がFalse → 相討ち
            self.alive = False
            other_piece.alive = False
            print(f"結果: 相討ち（i_win={i_win}, they_win={they_win}）")
            return "draw"

def create_initial_pieces(player):
    """プレイヤーの初期駒を作成"""
    pieces = []
    
    for piece_type, count in INITIAL_PIECE_COUNTS.items():
        for _ in range(count):
            piece = Piece(piece_type, player)
            pieces.append(piece)
    
    return pieces
