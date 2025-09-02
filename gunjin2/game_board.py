# -*- coding: utf-8 -*-
"""
軍人将棋 - ゲーム盤面管理
"""

from constants import *
from pieces import Piece, create_initial_pieces
import random

class GameBoard:
    """ゲーム盤面を管理するクラス"""
    
    def __init__(self):
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.player1_pieces = []
        self.player2_pieces = []
        self.current_player = PLAYER1
        self.game_state = GAME_STATE_WAITING
        self.setup_complete = {PLAYER1: False, PLAYER2: False}
        self.winner = None
        self.win_reason = None
        
    def reset(self):
        """盤面をリセット"""
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.player1_pieces = []
        self.player2_pieces = []
        self.current_player = PLAYER1
        self.game_state = GAME_STATE_WAITING
        self.setup_complete = {PLAYER1: False, PLAYER2: False}
        self.winner = None
        self.win_reason = None
        
    def get_piece_at(self, x, y):
        """指定位置の駒を取得"""
        if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
            return self.board[y][x]
        return None
        
    def set_piece_at(self, x, y, piece):
        """指定位置に駒を配置"""
        if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
            self.board[y][x] = piece
            if piece is not None:
                piece.set_position(x, y)
                
    def remove_piece_at(self, x, y):
        """指定位置の駒を除去"""
        piece = self.get_piece_at(x, y)
        if piece is not None:
            self.board[y][x] = None
            # プレイヤーの駒リストからも除去（既に除去済みの場合はスキップ）
            try:
                if piece.player == PLAYER1:
                    if piece in self.player1_pieces:
                        self.player1_pieces.remove(piece)
                else:
                    if piece in self.player2_pieces:
                        self.player2_pieces.remove(piece)
            except ValueError as e:
                print(f"駒削除エラー: {e} - 駒({piece.piece_type}, プレイヤー{piece.player}) at ({x}, {y})")
        return piece
        
    def move_piece(self, from_x, from_y, to_x, to_y):
        """駒を移動（戦闘判定含む）"""
        piece = self.get_piece_at(from_x, from_y)
        if piece is None:
            return {"success": False, "error": "移動する駒がありません"}
            
        # 移動可能性チェック
        valid_moves = piece.get_valid_moves(self)
        if (to_x, to_y) not in valid_moves:
            return {"success": False, "error": "無効な移動です"}
            
        # 移動先の駒をチェック
        target_piece = self.get_piece_at(to_x, to_y)
        battle_result = None
        
        if target_piece is not None:
            # 戦闘発生
            battle_result = self._execute_battle(piece, target_piece)
            
        else:
            # 通常移動
            self.remove_piece_at(from_x, from_y)
            self.set_piece_at(to_x, to_y, piece)
            
        # 勝利条件チェック
        self._check_victory_conditions()
        
        return {
            "success": True,
            "from": (from_x, from_y),
            "to": (to_x, to_y),
            "battle": battle_result
        }
        
    def _execute_battle(self, attacker, defender):
        """戦闘実行"""
        battle_result = attacker.battle(defender, self)
        
        result_data = {
            "position": (defender.x, defender.y),
            "attacker": {"player": attacker.player, "piece_type": attacker.piece_type},
            "defender": {"player": defender.player, "piece_type": defender.piece_type},
            "result": battle_result
        }
        
        if battle_result == BATTLE_WIN:
            # 攻撃側勝利
            self.remove_piece_at(defender.x, defender.y)
            self.remove_piece_at(attacker.x, attacker.y)
            self.set_piece_at(defender.x, defender.y, attacker)
            result_data["survivors"] = [attacker.to_dict()]
            
        elif battle_result == BATTLE_LOSE:
            # 攻撃側敗北
            self.remove_piece_at(attacker.x, attacker.y)
            result_data["survivors"] = [defender.to_dict()]
            
        else:  # BATTLE_DRAW
            # 相討ち
            self.remove_piece_at(attacker.x, attacker.y)
            self.remove_piece_at(defender.x, defender.y)
            result_data["survivors"] = []
            
        return result_data
        
    def place_piece_setup(self, player, piece_type, x, y):
        """配置フェーズでの駒配置"""
        if self.game_state != GAME_STATE_SETUP:
            return {"success": False, "error": "配置フェーズではありません"}
            
        # 配置エリアチェック
        if player == PLAYER1 and (x, y) not in PLAYER1_SETUP_AREA:
            return {"success": False, "error": "自陣以外には配置できません"}
        elif player == PLAYER2 and (x, y) not in PLAYER2_SETUP_AREA:
            return {"success": False, "error": "自陣以外には配置できません"}
            
        # 既に駒がある場合はチェック
        if self.get_piece_at(x, y) is not None:
            return {"success": False, "error": "既に駒があります"}
            
        # 未配置の駒があるかチェック
        available_pieces = self.get_unplaced_pieces(player)
        target_piece = None
        for piece in available_pieces:
            if piece.piece_type == piece_type:
                target_piece = piece
                break
                
        if target_piece is None:
            return {"success": False, "error": "配置可能な駒がありません"}
            
        # 駒を配置
        self.set_piece_at(x, y, target_piece)
        
        return {"success": True, "piece": target_piece}
        
    def remove_piece_setup(self, player, x, y):
        """配置フェーズでの駒除去"""
        if self.game_state != GAME_STATE_SETUP:
            return {"success": False, "error": "配置フェーズではありません"}
            
        piece = self.get_piece_at(x, y)
        if piece is None or piece.player != player:
            return {"success": False, "error": "除去する駒がありません"}
            
        self.remove_piece_at(x, y)
        # 除去した駒は未配置リストに戻る
        
        return {"success": True, "piece": piece}
        
    def auto_place_pieces(self, player):
        """駒の自動配置"""
        print(f"自動配置開始: プレイヤー{player}")
        
        available_pieces = self.get_unplaced_pieces(player)
        print(f"未配置駒数: {len(available_pieces)}")
        
        if not available_pieces:
            print("配置する駒がありません")
            return {"success": False, "error": "配置する駒がありません"}
            
        # 配置エリアを取得
        setup_area = PLAYER1_SETUP_AREA if player == PLAYER1 else PLAYER2_SETUP_AREA
        available_positions = [(x, y) for x, y in setup_area if self.get_piece_at(x, y) is None]
        print(f"利用可能な配置位置数: {len(available_positions)}")
        
        if len(available_positions) < len(available_pieces):
            print(f"配置スペースが不足: 必要{len(available_pieces)}, 利用可能{len(available_positions)}")
            return {"success": False, "error": "配置スペースが不足しています"}
            
        # ランダムに配置
        random.shuffle(available_positions)
        for i, piece in enumerate(available_pieces):
            x, y = available_positions[i]
            self.set_piece_at(x, y, piece)
            print(f"駒配置: {piece.name} at ({x}, {y})")
            
        print(f"自動配置完了: {len(available_pieces)}個の駒を配置")
        return {"success": True, "count": len(available_pieces)}
        
    def complete_setup(self, player):
        """配置完了"""
        unplaced = self.get_unplaced_pieces(player)
        if unplaced:
            return {"success": False, "error": f"{len(unplaced)}個の駒が未配置です"}
            
        self.setup_complete[player] = True
        
        # 両プレイヤーが完了したらゲーム開始
        if all(self.setup_complete.values()):
            self.game_state = GAME_STATE_PLAYING
            self.current_player = PLAYER1
            
        return {"success": True, "game_started": self.game_state == GAME_STATE_PLAYING}
        
    def get_unplaced_pieces(self, player):
        """未配置の駒リストを取得"""
        pieces = self.player1_pieces if player == PLAYER1 else self.player2_pieces
        return [piece for piece in pieces if piece.x is None]
        
    def get_remaining_pieces_count(self, player):
        """残り駒数を種類別に取得"""
        unplaced = self.get_unplaced_pieces(player)
        count = {}
        for piece_type in PIECE_TYPES.keys():
            count[piece_type] = len([p for p in unplaced if p.piece_type == piece_type])
        return count
        
    def initialize_setup_phase(self):
        """配置フェーズを開始"""
        self.game_state = GAME_STATE_SETUP
        self.player1_pieces = create_initial_pieces(PLAYER1)
        self.player2_pieces = create_initial_pieces(PLAYER2)
        self.setup_complete = {PLAYER1: False, PLAYER2: False}
        
    def switch_turn(self):
        """ターンを交代"""
        if self.current_player == PLAYER1:
            self.current_player = PLAYER2
        else:
            self.current_player = PLAYER1
            
    def _check_victory_conditions(self):
        """勝利条件をチェック"""
        # 司令部占拠チェック
        for hq_pos in PLAYER1_HEADQUARTERS:
            piece = self.get_piece_at(hq_pos[0], hq_pos[1])
            if piece is not None and piece.player == PLAYER2 and piece.can_occupy_headquarters():
                self.winner = PLAYER2
                self.win_reason = WIN_REASON_HEADQUARTERS
                self.game_state = GAME_STATE_FINISHED
                return
                
        for hq_pos in PLAYER2_HEADQUARTERS:
            piece = self.get_piece_at(hq_pos[0], hq_pos[1])
            if piece is not None and piece.player == PLAYER1 and piece.can_occupy_headquarters():
                self.winner = PLAYER1
                self.win_reason = WIN_REASON_HEADQUARTERS
                self.game_state = GAME_STATE_FINISHED
                return
                
        # 全滅チェック
        player1_movable = self._count_movable_pieces(PLAYER1)
        player2_movable = self._count_movable_pieces(PLAYER2)
        
        if player1_movable == 0:
            self.winner = PLAYER2
            self.win_reason = WIN_REASON_ELIMINATION
            self.game_state = GAME_STATE_FINISHED
        elif player2_movable == 0:
            self.winner = PLAYER1
            self.win_reason = WIN_REASON_ELIMINATION
            self.game_state = GAME_STATE_FINISHED
            
    def _count_movable_pieces(self, player):
        """移動可能な駒の数をカウント"""
        count = 0
        pieces = self.player1_pieces if player == PLAYER1 else self.player2_pieces
        for piece in pieces:
            if piece.x is not None and piece.is_movable:
                valid_moves = piece.get_valid_moves(self)
                if valid_moves:
                    count += 1
        return count
        
    def get_board_state(self, viewing_player=None):
        """盤面状態を取得（視点による情報隠蔽）"""
        board_state = []
        
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                piece = self.get_piece_at(x, y)
                if piece is not None:
                    piece_data = {
                        "x": x,
                        "y": y,
                        "player": piece.player
                    }
                    
                    # 視点による情報隠蔽
                    if viewing_player is None or piece.player == viewing_player:
                        piece_data["piece_type"] = piece.piece_type
                    else:
                        piece_data["piece_type"] = None
                        
                    board_state.append(piece_data)
                    
        return board_state
        
    def get_game_state_data(self):
        """ゲーム状態データを取得（JSONシリアライズ対応）"""
        # 盤面データを辞書形式で取得
        board_data = self.to_dict()
        
        # 従来の形式も含めて互換性を保持
        return {
            "state": self.game_state,
            "current_player": self.current_player,
            "winner": self.winner,
            "win_reason": self.win_reason,
            "setup_status": {
                "player1_complete": self.setup_complete[PLAYER1],
                "player2_complete": self.setup_complete[PLAYER2]
            },
            # 新しい盤面データ形式を追加
            "board_data": board_data
        }
        
    def can_move(self, player, from_x, from_y):
        """指定の駒が移動可能かチェック"""
        if self.game_state != GAME_STATE_PLAYING:
            return False
            
        if self.current_player != player:
            return False
            
        piece = self.get_piece_at(from_x, from_y)
        if piece is None or piece.player != player:
            return False
            
        return len(piece.get_valid_moves(self)) > 0
    
    def to_dict(self):
        """ゲーム盤面をJSONシリアライズ可能な辞書に変換"""
        # 盤面の駒情報を辞書形式に変換
        board_data = []
        for y in range(BOARD_HEIGHT):
            row = []
            for x in range(BOARD_WIDTH):
                piece = self.board[y][x]
                if piece is None:
                    row.append(None)
                else:
                    row.append(piece.to_dict())
            board_data.append(row)
        
        return {
            'board': board_data,
            'current_player': self.current_player,
            'game_state': self.game_state,
            'setup_complete': self.setup_complete,
            'winner': self.winner,
            'win_reason': self.win_reason
        }
    
    def from_dict(self, data):
        """辞書からゲーム盤面を復元"""
        from pieces import Piece
        
        # 盤面を復元
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.player1_pieces = []
        self.player2_pieces = []
        
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                piece_data = data['board'][y][x]
                if piece_data is not None:
                    piece = Piece.from_dict(piece_data)
                    self.board[y][x] = piece
                    if piece.player == PLAYER1:
                        self.player1_pieces.append(piece)
                    else:
                        self.player2_pieces.append(piece)
        
        # その他の状態を復元
        self.current_player = data['current_player']
        self.game_state = data['game_state']
        self.setup_complete = data['setup_complete']
        self.winner = data['winner']
        self.win_reason = data['win_reason']
