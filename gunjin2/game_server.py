# -*- coding: utf-8 -*-
"""
軍人将棋 - ゲームサーバー
"""

from network import GameServer
from game_board import GameBoard
from constants import *
import threading
import time

class GunjinServer:
    """軍人将棋サーバー"""
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.network = GameServer(host, port)
        self.board = GameBoard()
        self.running = False
        
        # ネットワークハンドラを登録
        self.network.register_handler(MSG_CLIENT_CONNECT, self.handle_client_connect)
        self.network.register_handler(MSG_SETUP_REQUEST, self.handle_setup_request)
        self.network.register_handler(MSG_MOVE_REQUEST, self.handle_move_request)
        self.network.register_handler(MSG_DISCONNECT, self.handle_disconnect)
        
    def start(self):
        """サーバー開始"""
        if not self.network.start_server():
            return False
            
        self.running = True
        print("軍人将棋サーバーが開始されました")
        
        return True
        
    def stop(self):
        """サーバー停止"""
        self.running = False
        self.network.stop_server()
        print("軍人将棋サーバーが停止されました")
        
    def handle_client_connect(self, client_id, message):
        """クライアント接続処理"""
        connection = self.network.connections.get(client_id)
        if not connection:
            return
            
        # 既に割り当て済みの場合はスキップ
        if hasattr(connection, 'player_id') and connection.player_id is not None:
            print(f"Client ID {client_id} は既にプレイヤー{connection.player_id}として割り当て済み")
            return
            
        # ゲーム終了状態の場合はリセット
        connected_player_count = len([c for c in self.network.connections.values() 
                                     if hasattr(c, 'player_id') and c.player_id is not None])
        print(f"現在の接続プレイヤー数: {connected_player_count}")
        
        if (self.board.game_state == GAME_STATE_FINISHED or connected_player_count == 0):
            print("ゲーム状態をリセットします")
            self.board.reset()
            
        # プレイヤーID割り当て（既に使用されているIDは避ける）
        used_player_ids = set()
        for client_id_iter, conn in self.network.connections.items():
            if hasattr(conn, 'player_id') and conn.player_id is not None:
                used_player_ids.add(conn.player_id)
                print(f"既存接続: Client ID {client_id_iter} -> プレイヤー{conn.player_id}")
        
        print(f"使用済みプレイヤーID: {used_player_ids}")
        
        if PLAYER1 not in used_player_ids:
            player_id = PLAYER1
        elif PLAYER2 not in used_player_ids:
            player_id = PLAYER2
        else:
            # 既に2人いる場合は接続拒否
            print(f"サーバーが満員: {used_player_ids}")
            self._send_error(client_id, ERROR_CONNECTION_FULL, "サーバーが満員です")
            return
            
        connection.player_id = player_id
        print(f"プレイヤー{player_id}が接続しました (Client ID: {client_id})")
        print(f"Client ID {client_id} の player_id を {player_id} に設定しました")
        
        # 2人目の接続時に配置フェーズ開始
        connected_players = len([c for c in self.network.connections.values() 
                                if hasattr(c, 'player_id') and c.player_id is not None])
        if connected_players == MAX_CONNECTIONS:
            print("2人のプレイヤーが接続しました。配置フェーズを開始します。")
            self.board.initialize_setup_phase()
            self._broadcast_game_state()
        
        # 接続受諾応答
        response = {
            "type": MSG_CONNECTION_ACCEPTED,
            "data": {
                "player_id": player_id,
                "game_state": self.board.game_state,
                "message": f"プレイヤー{player_id}として接続しました"
            }
        }
        self.network.send_to_client(client_id, response)
        
        # 2人揃ったら配置フェーズ開始
        active_players = len([conn for conn in self.network.connections.values() 
                            if hasattr(conn, 'player_id') and conn.player_id is not None])
        if active_players == MAX_CONNECTIONS and self.board.game_state == GAME_STATE_WAITING:
            print("2人揃いました。配置フェーズを開始します。")
            self.board.initialize_setup_phase()
            self._broadcast_game_state()
            
    def handle_setup_request(self, client_id, message):
        """配置リクエスト処理"""
        connection = self.network.connections.get(client_id)
        if not connection:
            print(f"エラー: Client ID {client_id} の接続が見つかりません")
            return
            
        player_id = getattr(connection, 'player_id', None)
        if player_id is None:
            print(f"エラー: Client ID {client_id} のプレイヤーIDが設定されていません")
            return
            
        data = message.get("data", {})
        action = data.get("action")
        
        print(f"配置リクエスト受信: Client ID {client_id}, プレイヤー{player_id}, アクション: {action}")
        
        try:
            if action == "place":
                # 駒配置
                piece_type = data.get("piece_type")
                position = data.get("position")
                
                result = self.board.place_piece_setup(
                    player_id, piece_type, position["x"], position["y"]
                )
                
                if result["success"]:
                    self._broadcast_setup_update(player_id)
                else:
                    self._send_error(client_id, ERROR_INVALID_MOVE, result["error"])
                    
            elif action == "remove":
                # 駒除去
                position = data.get("position")
                result = self.board.remove_piece_setup(
                    player_id, position["x"], position["y"]
                )
                
                if result["success"]:
                    self._broadcast_setup_update(player_id)
                else:
                    self._send_error(client_id, ERROR_INVALID_MOVE, result["error"])
                    
            elif action == "auto":
                # 自動配置
                print(f"プレイヤー{player_id} (Client ID: {client_id}) の自動配置リクエストを処理")
                result = self.board.auto_place_pieces(player_id)
                
                if result["success"]:
                    print(f"プレイヤー{player_id}の自動配置が完了しました")
                    self._broadcast_setup_update(player_id)
                else:
                    print(f"プレイヤー{player_id}の自動配置が失敗: {result['error']}")
                    self._send_error(client_id, ERROR_INVALID_MOVE, result["error"])
                    
            elif action == "complete":
                # 配置完了
                result = self.board.complete_setup(player_id)
                
                if result["success"]:
                    self._broadcast_setup_update(player_id)
                    if result["game_started"]:
                        self._broadcast_game_state()
                else:
                    self._send_error(client_id, ERROR_SETUP_NOT_COMPLETE, result["error"])
                    
        except Exception as e:
            print(f"配置リクエスト処理エラー: {e}")
            self._send_error(client_id, ERROR_INVALID_MOVE, "配置処理でエラーが発生しました")
            
    def handle_move_request(self, client_id, message):
        """移動リクエスト処理"""
        connection = self.network.connections.get(client_id)
        if not connection:
            return
            
        player_id = connection.player_id
        data = message.get("data", {})
        
        try:
            # ターンチェック
            if self.board.current_player != player_id:
                self._send_error(client_id, ERROR_NOT_YOUR_TURN, "あなたのターンではありません")
                return
                
            # ゲーム状態チェック
            if self.board.game_state != GAME_STATE_PLAYING:
                self._send_error(client_id, ERROR_GAME_NOT_STARTED, "ゲームが開始されていません")
                return
                
            # 移動実行
            from_pos = data.get("from")
            to_pos = data.get("to")
            
            result = self.board.move_piece(
                from_pos["x"], from_pos["y"],
                to_pos["x"], to_pos["y"]
            )
            
            if result["success"]:
                # 成功：全クライアントに更新を配信
                self._broadcast_game_update(result)
                
                # 戦闘が発生した場合
                if result.get("battle"):
                    self._broadcast_battle_result(result["battle"])
                    
                # ターン交代
                self.board.switch_turn()
                
                # 勝利判定
                if self.board.game_state == GAME_STATE_FINISHED:
                    self._broadcast_game_state()
                else:
                    self._broadcast_game_state()
                    
            else:
                self._send_error(client_id, ERROR_INVALID_MOVE, result["error"])
                
        except Exception as e:
            print(f"移動リクエスト処理エラー: {e}")
            self._send_error(client_id, ERROR_INVALID_MOVE, "移動処理でエラーが発生しました")
            
    def handle_disconnect(self, client_id, message):
        """切断処理"""
        connection = self.network.connections.get(client_id)
        if connection:
            player_id = connection.player_id
            
            # ゲーム中の場合は相手の勝利
            if self.board.game_state in [GAME_STATE_SETUP, GAME_STATE_PLAYING]:
                winner = PLAYER2 if player_id == PLAYER1 else PLAYER1
                self.board.winner = winner
                self.board.win_reason = WIN_REASON_DISCONNECT
                self.board.game_state = GAME_STATE_FINISHED
                
                self._broadcast_game_state()
                
    def _broadcast_setup_update(self, player_id):
        """配置更新をブロードキャスト"""
        for client_id, connection in self.network.connections.items():
            viewing_player = connection.player_id
            
            # プレイヤー視点でのデータを作成
            update_data = {
                "player": player_id,
                "setup_complete": self.board.setup_complete[player_id],
                "remaining_pieces": self.board.get_remaining_pieces_count(viewing_player),
                "visible_positions": self._get_visible_positions(viewing_player)
            }
            
            message = {
                "type": MSG_SETUP_UPDATE,
                "data": update_data
            }
            
            self.network.send_to_client(client_id, message)
            
    def _broadcast_game_update(self, move_result):
        """ゲーム更新をブロードキャスト"""
        for client_id, connection in self.network.connections.items():
            viewing_player = connection.player_id
            
            update_data = {
                "move_result": {
                    "success": move_result["success"],
                    "from": move_result["from"],
                    "to": move_result["to"],
                    "battle": move_result.get("battle")
                },
                "current_player": self.board.current_player,
                "board_state": self.board.get_board_state(viewing_player)
            }
            
            message = {
                "type": MSG_GAME_UPDATE,
                "data": update_data
            }
            
            self.network.send_to_client(client_id, message)
            
    def _broadcast_battle_result(self, battle_data):
        """戦闘結果をブロードキャスト"""
        for client_id, connection in self.network.connections.items():
            viewing_player = connection.player_id
            
            # 視点による情報隠蔽
            battle_result = {
                "position": battle_data["position"],
                "result": battle_data["result"],
                "survivors": []
            }
            
            # 攻撃側情報（攻撃者にのみ駒種類を通知）
            attacker_info = {
                "player": battle_data["attacker"]["player"],
                "piece_type": battle_data["attacker"]["piece_type"] if battle_data["attacker"]["player"] == viewing_player else None
            }
            battle_result["attacker"] = attacker_info
            
            # 守備側情報（守備者にのみ駒種類を通知）
            defender_info = {
                "player": battle_data["defender"]["player"], 
                "piece_type": battle_data["defender"]["piece_type"] if battle_data["defender"]["player"] == viewing_player else None
            }
            battle_result["defender"] = defender_info
            
            # 生存者情報
            for survivor in battle_data["survivors"]:
                # survivorは既に辞書形式（to_dict()の結果）
                survivor_info = {
                    "player": survivor["player"],
                    "piece_type": survivor["piece_type"] if survivor["player"] == viewing_player else None
                }
                battle_result["survivors"].append(survivor_info)
                
            message = {
                "type": MSG_BATTLE_RESULT,
                "data": battle_result
            }
            
            self.network.send_to_client(client_id, message)
            
    def _broadcast_game_state(self):
        """ゲーム状態をブロードキャスト"""
        state_data = self.board.get_game_state_data()
        
        message = {
            "type": MSG_GAME_STATE,
            "data": state_data
        }
        
        self.network.broadcast_message(message)
        
    def _get_visible_positions(self, viewing_player):
        """視点別の見える駒位置を取得"""
        positions = []
        
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                piece = self.board.get_piece_at(x, y)
                if piece is not None:
                    pos_data = {
                        "x": x,
                        "y": y,
                        "player": piece.player
                    }
                    
                    # 自分の駒のみ種類を表示
                    if piece.player == viewing_player:
                        pos_data["piece_type"] = piece.piece_type
                    else:
                        pos_data["piece_type"] = None
                        
                    positions.append(pos_data)
                    
        return positions
        
    def _send_error(self, client_id, error_code, message):
        """エラーメッセージを送信"""
        error_message = {
            "type": MSG_ERROR,
            "data": {
                "code": error_code,
                "message": message
            }
        }
        self.network.send_to_client(client_id, error_message)


def main():
    """サーバーメイン関数"""
    server = GunjinServer()
    
    if not server.start():
        print("サーバー開始に失敗しました")
        return
        
    try:
        # サーバーループ
        while server.running:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nサーバーを停止します...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
