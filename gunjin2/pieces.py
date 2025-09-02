# -*- coding: utf-8 -*-
"""
軍人将棋 - 駒クラス定義
"""

from constants import *

class Piece:
    """駒の基本クラス"""
    
    def __init__(self, piece_type, player, x=None, y=None):
        self.piece_type = piece_type
        self.player = player
        self.x = x
        self.y = y
        self.info = PIECE_TYPES[piece_type]
        
    @property
    def name(self):
        """駒の名前を取得"""
        return self.info["name"]
    
    @property
    def rank(self):
        """駒のランクを取得"""
        return self.info["rank"]
    
    @property
    def is_movable(self):
        """駒が移動可能かどうか"""
        return self.info["movable"]
    
    @property
    def position(self):
        """駒の位置を取得"""
        return (self.x, self.y)
    
    def set_position(self, x, y):
        """駒の位置を設定"""
        self.x = x
        self.y = y
    
    def to_dict(self):
        """駒をJSONシリアライズ可能な辞書に変換"""
        return {
            'piece_type': self.piece_type,
            'player': self.player,
            'x': self.x,
            'y': self.y
        }
    
    @classmethod
    def from_dict(cls, data):
        """辞書から駒オブジェクトを作成"""
        return cls(
            piece_type=data['piece_type'],
            player=data['player'],
            x=data['x'],
            y=data['y']
        )
        
    def get_valid_moves(self, board):
        """この駒が移動可能な位置のリストを取得"""
        if not self.is_movable:
            return []
        
        valid_moves = []
        
        # 駒の種類に応じた移動判定
        if self.piece_type in [1, 2, 3, 4, 5, 6, 7, 8, 9, 14]:  # 基本駒（将官・佐官・尉官・スパイ）
            valid_moves = self._get_basic_moves(board)
        elif self.piece_type in [11, 12]:  # タンク・騎兵
            valid_moves = self._get_tank_cavalry_moves(board)
        elif self.piece_type == 10:  # 飛行機
            valid_moves = self._get_airplane_moves(board)
        elif self.piece_type == 13:  # 工兵
            valid_moves = self._get_engineer_moves(board)
            
        return valid_moves
    
    def _get_basic_moves(self, board):
        """基本駒（将官・佐官・尉官・スパイ）の移動可能位置"""
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # 上下左右
        
        for dx, dy in directions:
            new_x, new_y = self.x + dx, self.y + dy
            if self._is_valid_move(board, new_x, new_y):
                moves.append((new_x, new_y))
                
        return moves
    
    def _get_tank_cavalry_moves(self, board):
        """タンク・騎兵の移動可能位置（1マスまたは2マス前）"""
        moves = []
        
        # 基本移動（前後左右1マス）
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            new_x, new_y = self.x + dx, self.y + dy
            if self._is_valid_move(board, new_x, new_y):
                moves.append((new_x, new_y))
        
        # 2マス前への移動（手前に駒がない場合）
        forward_dy = -1 if self.player == PLAYER1 else 1
        one_step = (self.x, self.y + forward_dy)
        two_steps = (self.x, self.y + 2 * forward_dy)
        
        # 1マス前が空で、2マス前が有効な移動先の場合
        if (self._is_valid_position(one_step[0], one_step[1]) and 
            board.get_piece_at(one_step[0], one_step[1]) is None and
            self._is_valid_move(board, two_steps[0], two_steps[1])):
            moves.append(two_steps)
            
        return moves
    
    def _get_airplane_moves(self, board):
        """飛行機の移動可能位置（縦無制限、横1マス、侵入不可領域無視）"""
        moves = []
        
        # 左右1マス
        for dx in [-1, 1]:
            new_x, new_y = self.x + dx, self.y
            if self._is_valid_position(new_x, new_y):
                piece_at_dest = board.get_piece_at(new_x, new_y)
                if piece_at_dest is None or piece_at_dest.player != self.player:
                    moves.append((new_x, new_y))
        
        # 前後無制限（途中の駒を飛び越え可能、侵入不可領域も無視）
        for dy in [-1, 1]:
            for distance in range(1, BOARD_HEIGHT):
                new_x, new_y = self.x, self.y + dy * distance
                if not self._is_valid_position(new_x, new_y):
                    break
                    
                piece_at_dest = board.get_piece_at(new_x, new_y)
                if piece_at_dest is None:
                    # 空いているマス（侵入不可領域も無視）
                    moves.append((new_x, new_y))
                elif piece_at_dest.player != self.player:
                    # 敵の駒（戦闘可能）
                    moves.append((new_x, new_y))
                    break
                else:
                    # 味方の駒（移動不可）
                    break
                    
        return moves
    
    def _get_engineer_moves(self, board):
        """工兵の移動可能位置（直線移動、途中に駒があると停止）"""
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # 上下左右
        
        for dx, dy in directions:
            for distance in range(1, max(BOARD_WIDTH, BOARD_HEIGHT)):
                new_x, new_y = self.x + dx * distance, self.y + dy * distance
                
                if not self._is_valid_position(new_x, new_y):
                    break
                    
                if not self._can_enter_position(new_x, new_y):
                    break
                    
                piece_at_dest = board.get_piece_at(new_x, new_y)
                if piece_at_dest is None:
                    # 空いているマス
                    moves.append((new_x, new_y))
                elif piece_at_dest.player != self.player:
                    # 敵の駒（戦闘可能）
                    moves.append((new_x, new_y))
                    break
                else:
                    # 味方の駒（移動不可）
                    break
                    
        return moves
    
    def _is_valid_move(self, board, x, y, ignore_neutral_zone=False):
        """指定位置への移動が有効かチェック"""
        # 盤面内チェック
        if not self._is_valid_position(x, y):
            return False
            
        # 侵入可能位置チェック（飛行機は侵入不可領域を無視）
        if not ignore_neutral_zone and not self._can_enter_position(x, y):
            return False
            
        # 移動先の駒チェック
        piece_at_dest = board.get_piece_at(x, y)
        if piece_at_dest is not None and piece_at_dest.player == self.player:
            return False  # 味方の駒がいる場合は移動不可
            
        return True
    
    def _is_valid_position(self, x, y):
        """位置が盤面内かチェック"""
        return 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT
    
    def _can_enter_position(self, x, y):
        """位置に侵入可能かチェック（侵入不可領域の制限）"""
        # プレイヤー1（下側）の場合
        if self.player == PLAYER1:
            if y < NEUTRAL_ZONE_Y:  # 敵陣への侵入
                # 突入口のみ通過可能（ただし滞在は不可）
                if y == NEUTRAL_ZONE_Y and (x, y) in BRIDGE_POSITIONS:
                    return False  # 橋の上は滞在不可
                # 突入口から敵陣に入る場合のみ可能
                return (x, NEUTRAL_ZONE_Y) in BRIDGE_POSITIONS
            return True
            
        # プレイヤー2（上側）の場合  
        elif self.player == PLAYER2:
            if y > NEUTRAL_ZONE_Y:  # 敵陣への侵入
                # 突入口のみ通過可能（ただし滞在は不可）
                if y == NEUTRAL_ZONE_Y and (x, y) in BRIDGE_POSITIONS:
                    return False  # 橋の上は滞在不可
                # 突入口から敵陣に入る場合のみ可能
                return (x, NEUTRAL_ZONE_Y) in BRIDGE_POSITIONS
            return True
            
        return True
    
    def battle(self, enemy_piece, board=None):
        """戦闘処理"""
        # 軍旗の特殊処理
        if enemy_piece.piece_type == 16:  # 相手が軍旗
            return self._battle_against_flag(enemy_piece, board)
        elif self.piece_type == 16:  # 自分が軍旗
            return enemy_piece._battle_against_flag(self, board) * -1
            
        # 通常の戦闘
        result = BATTLE_TABLE.get(self.piece_type, {}).get(enemy_piece.piece_type, 0)
        return result
    
    def _battle_against_flag(self, flag_piece, board):
        """軍旗との戦闘処理"""
        if board is None:
            return 1  # 軍旗単体では全ての駒に負ける
            
        # 軍旗の後ろの駒を確認
        behind_x, behind_y = flag_piece.x, flag_piece.y + (1 if flag_piece.player == PLAYER1 else -1)
        behind_piece = board.get_piece_at(behind_x, behind_y)
        
        if behind_piece is not None and behind_piece.player == flag_piece.player:
            # 後ろに味方の駒がある場合、その駒の威力で戦闘
            virtual_battle_result = BATTLE_TABLE.get(self.piece_type, {}).get(behind_piece.piece_type, 0)
            return virtual_battle_result
        else:
            # 後ろに駒がない場合、軍旗は全ての駒に負ける
            return 1
    
    def can_occupy_headquarters(self):
        """司令部を占拠可能かチェック"""
        return self.piece_type in COMMANDER_PIECES
    
    def __str__(self):
        return f"{self.name}({self.player})"
    
    def __repr__(self):
        return f"Piece(type={self.piece_type}, player={self.player}, pos=({self.x},{self.y}))"


def create_initial_pieces(player):
    """プレイヤーの初期駒セットを作成"""
    pieces = []
    
    for piece_type, info in PIECE_TYPES.items():
        count = info["count"]
        for _ in range(count):
            pieces.append(Piece(piece_type, player))
            
    return pieces


def get_piece_display_name(piece_type, player, viewing_player):
    """表示用の駒名を取得（視点による隠蔽処理）"""
    if player == viewing_player:
        # 自分の駒は種類を表示
        return PIECE_TYPES[piece_type]["name"]
    else:
        # 相手の駒は「？」で表示
        return "？"


def get_piece_display_color(piece_type, player, viewing_player):
    """表示用の駒色を取得"""
    if player == viewing_player:
        # 自分の駒はプレイヤー色
        return PLAYER1_COLOR if player == PLAYER1 else PLAYER2_COLOR
    else:
        # 相手の駒はグレー
        return ENEMY_PIECE_COLOR
