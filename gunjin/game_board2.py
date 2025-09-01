"""
ゲーム盤面管理
"""

import random
from constants import *
from pieces import create_initial_pieces

class GameBoard:
    """ゲーム盤面クラス"""
    
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(6)]  # 8x6盤面
        self.current_player = 1  # プレイヤー1から開始
        self.game_state = "setup"
        self.selected_piece = None
        self.selected_pos = None
        self.valid_moves = []
        self.battle_log = []
        self.setup_complete = {1: False, 2: False}
        
    def get_piece_at(self, x, y):
        """指定座標の駒を取得"""
        if 0 <= x < 8 and 0 <= y < 6:
            return self.board[y][x]
        return None
    
    def set_piece_at(self, x, y, piece):
        """指定座標に駒を配置"""
        if 0 <= x < 8 and 0 <= y < 6:
            self.board[y][x] = piece
            if piece:
                piece.x = x
                piece.y = y
    
    def remove_piece_at(self, x, y):
        """指定座標の駒を削除"""
        piece = self.get_piece_at(x, y)
        if piece:
            self.board[y][x] = None
        return piece
    
    def is_valid_position(self, x, y):
        """座標が盤面内かチェック"""
        return 0 <= x < 8 and 0 <= y < 6
    
    def get_setup_area(self, player):
        """プレイヤーのセットアップエリアを取得"""
        setup_positions = []
        if player == 1:
            # プレイヤー1は下半分（y=3,4,5）
            for y in range(3, 6):
                for x in range(8):
                    setup_positions.append((x, y))
        else:
            # プレイヤー2は上半分（y=0,1,2）
            for y in range(3):
                for x in range(8):
                    setup_positions.append((x, y))
        return setup_positions
    
    def get_headquarters(self, player):
        """プレイヤーの総司令部座標を取得"""
        if player == 1:
            # プレイヤー1の総司令部は最下段中央2マス
            return [(3, 5), (4, 5)]
        else:
            # プレイヤー2の総司令部は最上段中央2マス
            return [(3, 0), (4, 0)]
    
    def is_headquarters_occupied(self, player):
        """総司令部が占領されているかチェック"""
        headquarters = self.get_headquarters(player)
        command_pieces = ["総司令", "軍司令", "師団長", "連隊長"]
        
        for x, y in headquarters:
            piece = self.get_piece_at(x, y)
            if piece and piece.player != player and piece.piece_type in command_pieces:
                return True
        return False
    
    def move_piece(self, from_x, from_y, to_x, to_y):
        """駒を移動"""
        piece = self.get_piece_at(from_x, from_y)
        target_piece = self.get_piece_at(to_x, to_y)
        
        if not piece:
            return False, "移動する駒がありません"
        
        if piece.player != self.current_player:
            return False, "自分のターンではありません"
        
        if not self.is_valid_move(piece, to_x, to_y):
            return False, "無効な移動です"
        
        # 戦闘が発生する場合
        if target_piece and target_piece.player != piece.player:
            battle_result = piece.battle(target_piece)
            
            battle_info = {
                'attacker': piece,
                'defender': target_piece,
                'result': battle_result,
                'position': (to_x, to_y)
            }
            self.battle_log.append(battle_info)
            
            if battle_result == "win":
                self.remove_piece_at(to_x, to_y)
                self.remove_piece_at(from_x, from_y)
                self.set_piece_at(to_x, to_y, piece)
            elif battle_result == "lose":
                self.remove_piece_at(from_x, from_y)
            elif battle_result == "draw":
                self.remove_piece_at(from_x, from_y)
                self.remove_piece_at(to_x, to_y)
        else:
            # 通常の移動
            self.remove_piece_at(from_x, from_y)
            self.set_piece_at(to_x, to_y, piece)
        
        # ターン交代
        self.current_player = 2 if self.current_player == 1 else 1
        self.selected_piece = None
        self.selected_pos = None
        self.valid_moves = []
        
        # 勝利条件チェック
        if self.check_victory():
            self.game_state = "game_over"
        
        return True, "移動完了"
    
    def is_valid_move(self, piece, to_x, to_y):
        """移動が有効かチェック"""
        if not self.is_valid_position(to_x, to_y):
            return False
        
        # 自分の駒がある場所には移動できない
        target_piece = self.get_piece_at(to_x, to_y)
        if target_piece and target_piece.player == piece.player:
            return False
        
        # 駒の種類に応じた移動ルール
        return self._check_piece_movement(piece, to_x, to_y)
    
    def _check_piece_movement(self, piece, to_x, to_y):
        """駒の移動ルールをチェック"""
        from_x, from_y = piece.x, piece.y
        dx = abs(to_x - from_x)
        dy = abs(to_y - from_y)
        
        # 基本駒（将官・佐官・尉官・スパイ）
        basic_pieces = ["総司令", "軍司令", "師団長", "連隊長", "大隊長", "中隊長", 
                       "小隊長", "分隊長", "兵長", "スパイ"]
        
        if piece.piece_type in basic_pieces:
            # 前後左右1マス
            return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)
        
        elif piece.piece_type in ["戦車", "騎兵"]:
            # 前後左右1マス、または2マス前
            if (dx == 1 and dy == 0) or (dx == 0 and dy == 1):
                return True
            # 2マス前（手前に駒がない場合のみ）
            if dx == 0 and dy == 2:
                mid_y = (from_y + to_y) // 2
                return self.get_piece_at(from_x, mid_y) is None
            return False
        
        elif piece.piece_type == "航空機":
            # 前後何マスでも、左右1マス
            if dx == 0:  # 前後移動
                return self._is_path_clear(from_x, from_y, to_x, to_y)
            elif dy == 0 and dx == 1:  # 左右1マス
                return True
            return False
        
        elif piece.piece_type == "工兵":
            # 前後左右何マスでも（飛車の動き）
            if dx == 0 or dy == 0:
                return self._is_path_clear(from_x, from_y, to_x, to_y)
            return False
        
        # 移動不可駒（地雷・旗）
        return False
    
    def _is_path_clear(self, from_x, from_y, to_x, to_y):
        """移動経路に駒がないかチェック"""
        dx = 1 if to_x > from_x else -1 if to_x < from_x else 0
        dy = 1 if to_y > from_y else -1 if to_y < from_y else 0
        
        x, y = from_x + dx, from_y + dy
        while x != to_x or y != to_y:
            if self.get_piece_at(x, y) is not None:
                return False
            x += dx
            y += dy
        
        return True
    
    def get_valid_moves(self, piece):
        """駒の有効な移動先を取得"""
        valid_moves = []
        
        for y in range(6):
            for x in range(8):
                if self.is_valid_move(piece, x, y):
                    valid_moves.append((x, y))
        
        return valid_moves
    
    def select_piece(self, x, y):
        """駒を選択"""
        piece = self.get_piece_at(x, y)
        
        if not piece:
            self.selected_piece = None
            self.selected_pos = None
            self.valid_moves = []
            return False
        
        if piece.player != self.current_player:
            return False
        
        if not piece.can_move():
            return False
        
        self.selected_piece = piece
        self.selected_pos = (x, y)
        self.valid_moves = self.get_valid_moves(piece)
        return True
    
    def auto_setup(self, player):
        """自動配置"""
        pieces = create_initial_pieces(player)
        setup_area = self.get_setup_area(player)
        
        # 配置エリアをシャッフル
        available_positions = setup_area[:]
        random.shuffle(available_positions)
        
        # 駒を配置
        for i, piece in enumerate(pieces):
            if i < len(available_positions):
                x, y = available_positions[i]
                self.set_piece_at(x, y, piece)
    
    def check_victory(self):
        """勝利条件をチェック"""
        # 総司令部占領チェック
        for player in [1, 2]:
            if self.is_headquarters_occupied(player):
                return True
        
        # 移動可能駒の全滅チェック
        for player in [1, 2]:
            has_movable_pieces = False
            for y in range(6):
                for x in range(8):
                    piece = self.get_piece_at(x, y)
                    if piece and piece.player == player and piece.can_move():
                        if self.get_valid_moves(piece):
                            has_movable_pieces = True
                            break
                if has_movable_pieces:
                    break
            if not has_movable_pieces:
                return True
        
        return False
    
    def is_setup_complete(self):
        """セットアップが完了しているかチェック"""
        return all(self.setup_complete.values())
