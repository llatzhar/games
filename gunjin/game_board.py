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
        self.game_state = GAME_STATE_SETUP
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
        # READMEに基づく指揮駒（将官・佐官）
        command_pieces = ["大将", "中将", "少将", "大佐", "中佐", "少佐"]
        
        # 総司令部のいずれかのマスに敵の指揮駒があれば占領
        for x, y in headquarters:
            piece = self.get_piece_at(x, y)
            if piece and piece.player != player and piece.piece_type in command_pieces:
                print(f"総司令部占領検出: プレイヤー{player}の総司令部({x}, {y})に敵の{piece.piece_type}(プレイヤー{piece.player})がいます")
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
            print(f"戦闘発生: {piece.get_name()}({piece.player}) vs {target_piece.get_name()}({target_piece.player})")
            battle_result = piece.battle(target_piece)
            print(f"戦闘結果: {battle_result}")
            
            battle_info = {
                'attacker': piece,
                'defender': target_piece,
                'result': battle_result,
                'position': (to_x, to_y)
            }
            self.battle_log.append(battle_info)
            
            if battle_result == "win":
                # 攻撃側勝利：守備側を除去して攻撃側を移動
                self.remove_piece_at(to_x, to_y)  # 守備側除去
                self.remove_piece_at(from_x, from_y)  # 攻撃側を元の位置から除去
                piece.x, piece.y = to_x, to_y  # 駒の位置を更新
                self.set_piece_at(to_x, to_y, piece)  # 新しい位置に配置
            elif battle_result == "lose":
                # 攻撃側敗北：攻撃側のみ除去
                self.remove_piece_at(from_x, from_y)
            elif battle_result == "draw":
                # 相打ち：両方除去
                self.remove_piece_at(from_x, from_y)
                self.remove_piece_at(to_x, to_y)
        else:
            # 通常の移動
            print(f"通常の移動: {piece.get_name()}({piece.player}) ({from_x},{from_y}) → ({to_x},{to_y})")
            self.remove_piece_at(from_x, from_y)
            piece.x, piece.y = to_x, to_y  # 駒の位置を更新
            self.set_piece_at(to_x, to_y, piece)
        
        # ターン交代
        self.current_player = 2 if self.current_player == 1 else 1
        self.selected_piece = None
        self.selected_pos = None
        self.valid_moves = []
        
        # 勝利条件チェック（デバッグ用に一時無効化）
        # if self.check_victory():
        #     self.game_state = GAME_STATE_GAME_OVER
        
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
        basic_pieces = ["大将", "中将", "少将", "大佐", "中佐", "少佐", 
                       "大尉", "中尉", "少尉", "スパイ"]
        
        if piece.piece_type in basic_pieces:
            # 前後左右1マス
            return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)
        
        elif piece.piece_type in ["タンク", "騎兵"]:
            # 前後左右1マス、または2マス前
            if (dx == 1 and dy == 0) or (dx == 0 and dy == 1):
                return True
            # 2マス前（手前に駒がない場合のみ）
            if dx == 0 and dy == 2:
                mid_y = (from_y + to_y) // 2
                return self.get_piece_at(from_x, mid_y) is None
            return False
        
        elif piece.piece_type == "飛行機":
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
        """自動配置（総司令部には最大1駒まで）"""
        print(f"プレイヤー{player}の自動配置を開始")
        pieces = create_initial_pieces(player)
        print(f"作成された駒数: {len(pieces)}")
        
        setup_area = self.get_setup_area(player)
        headquarters = self.get_headquarters(player)
        
        print(f"セットアップエリア: {len(setup_area)}マス, 総司令部: {headquarters}")
        
        # 総司令部とそれ以外の配置エリアに分ける
        hq_positions = [pos for pos in setup_area if pos in headquarters]
        non_hq_positions = [pos for pos in setup_area if pos not in headquarters]
        
        print(f"総司令部座標: {len(hq_positions)}マス, 通常座標: {len(non_hq_positions)}マス")
        
        # 配置エリアをシャッフル
        random.shuffle(hq_positions)
        random.shuffle(non_hq_positions)
        
        # 総司令部には最大1駒のみ配置、残りは通常エリアに配置
        available_positions = []
        if hq_positions:
            available_positions.append(hq_positions[0])  # 総司令部の1マスのみ
        available_positions.extend(non_hq_positions)
        
        print(f"利用可能座標数: {len(available_positions)}")
        
        # 駒を配置
        placed_count = 0
        for i, piece in enumerate(pieces):
            if i < len(available_positions):
                x, y = available_positions[i]
                self.set_piece_at(x, y, piece)
                placed_count += 1
                
        print(f"配置完了: {placed_count}/{len(pieces)}個配置")
        
        # 配置後の確認
        board_count = 0
        for y in range(6):
            for x in range(8):
                piece = self.get_piece_at(x, y)
                if piece and piece.player == player:
                    board_count += 1
        print(f"盤面確認: プレイヤー{player}の駒が{board_count}個")
    
    def check_victory(self):
        """勝利条件をチェック"""
        # 一時的に勝利条件チェックを無効化してデバッグ
        print("勝利条件チェックが呼ばれました（現在無効化中）")
        return False
        
        # 総司令部占領チェック
        for player in [1, 2]:
            if self.is_headquarters_occupied(player):
                print(f"勝利条件満たす: プレイヤー{player}の総司令部が占領されました")
                return True
        
        # 移動可能駒の全滅チェック
        for player in [1, 2]:
            has_movable_pieces = False
            movable_count = 0
            total_count = 0
            for y in range(6):
                for x in range(8):
                    piece = self.get_piece_at(x, y)
                    if piece and piece.player == player:
                        total_count += 1
                        if piece.can_move():
                            valid_moves = self.get_valid_moves(piece)
                            if valid_moves:
                                has_movable_pieces = True
                                movable_count += 1
                                break
                if has_movable_pieces:
                    break
            print(f"プレイヤー{player}: 総駒数={total_count}, 移動可能駒数={movable_count}")
            if not has_movable_pieces:
                print(f"勝利条件満たす: プレイヤー{player}の駒が全滅しました")
                return True
        
        return False
    
    def is_setup_complete(self):
        """セットアップが完了しているかチェック"""
        return all(self.setup_complete.values())
