# -*- coding: utf-8 -*-
"""
軍人将棋 - メインゲームロジック（クライアント）
"""

import pygame
import sys
import argparse
from network import GameClient, get_local_ip
from ui import GameUI
from game_board import GameBoard
from constants import *
import threading
import time

class GunjinClient:
    """軍人将棋クライアント"""
    
    def __init__(self, server_host=None, server_port=DEFAULT_PORT):
        # サーバーホストが指定されていない場合は自動検出
        if server_host is None:
            server_host = get_local_ip()
            
        self.network = GameClient()
        self.ui = GameUI()
        self.board = GameBoard()  # 表示用ローカル盤面
        
        self.running = False
        self.my_player = None
        self.game_state = GAME_STATE_WAITING
        self.current_player = PLAYER1
        
        # サーバー接続先設定
        self.server_host = server_host
        self.server_port = server_port
        
        # ネットワークハンドラを登録
        self.network.register_handler(MSG_CONNECTION_ACCEPTED, self.handle_connection_accepted)
        self.network.register_handler(MSG_SETUP_UPDATE, self.handle_setup_update)
        self.network.register_handler(MSG_GAME_UPDATE, self.handle_game_update)
        self.network.register_handler(MSG_BATTLE_RESULT, self.handle_battle_result)
        self.network.register_handler(MSG_GAME_STATE, self.handle_game_state)
        self.network.register_handler(MSG_ERROR, self.handle_error)
        self.network.register_handler(MSG_PLAYER_DISCONNECTED, self.handle_player_disconnected)
        
        # UIイベントハンドラを登録
        self.ui.register_event_handler(pygame.MOUSEBUTTONDOWN, self.handle_mouse_click)
        self.ui.register_event_handler(pygame.KEYDOWN, self.handle_key_press)
        
    def initialize(self):
        """クライアント初期化"""
        if not self.ui.initialize():
            return False
            
        self.ui.set_screen("menu")
        print("クライアント初期化完了")
        return True
        
    def run(self):
        """メインループ"""
        self.running = True
        
        while self.running:
            if not self.ui.handle_events():
                break
                
            self.ui.update_display()
            
        self.cleanup()
        
    def cleanup(self):
        """リソース解放"""
        self.running = False
        self.network.disconnect()
        self.ui.cleanup()
        
    def connect_to_server(self, host, port):
        """サーバーに接続"""
        if self.network.connect_to_server(host, port):
            print("サーバーに接続中...")
            return True
        else:
            print("サーバーに接続できませんでした")
            return False
            
    def handle_mouse_click(self, event):
        """マウスクリック処理"""
        if event.button != 1:  # 左クリック以外は無視
            return
            
        mouse_pos = pygame.mouse.get_pos()
        
        if self.ui.current_screen == "menu":
            self.handle_menu_click(mouse_pos)
        elif self.ui.current_screen == "setup":
            self.handle_setup_click(mouse_pos)
        elif self.ui.current_screen == "game":
            self.handle_game_click(mouse_pos)
            
    def handle_key_press(self, event):
        """キーボード入力処理"""
        if event.key == pygame.K_ESCAPE:
            # ESCキーでメニューに戻る
            self.ui.set_screen("menu")
            
    def handle_menu_click(self, mouse_pos):
        """メニュー画面のクリック処理"""
        if self.ui.is_button_clicked("host_game", mouse_pos):
            self.host_game()
        elif self.ui.is_button_clicked("join_game", mouse_pos):
            self.join_game()
        elif self.ui.is_button_clicked("quit", mouse_pos):
            self.running = False
            
    def handle_setup_click(self, mouse_pos):
        """配置画面のクリック処理"""
        # ボタンクリック判定
        if self.ui.is_button_clicked("auto_place", mouse_pos):
            self.auto_place_pieces()
            return
        elif self.ui.is_button_clicked("complete_setup", mouse_pos):
            self.complete_setup()
            return
            
        # 盤面クリック判定
        board_pos = self.ui.get_board_position(mouse_pos)
        if board_pos is not None:
            self.handle_setup_board_click(board_pos)
            
    def handle_game_click(self, mouse_pos):
        """ゲーム画面のクリック処理"""
        board_pos = self.ui.get_board_position(mouse_pos)
        if board_pos is not None:
            self.handle_game_board_click(board_pos)
            
    def handle_setup_board_click(self, pos):
        """配置画面での盤面クリック"""
        x, y = pos
        piece = self.board.get_piece_at(x, y)
        
        if piece is not None and piece.player == self.my_player:
            # 自分の駒をクリック（除去）
            self.remove_piece(x, y)
        else:
            # 空のマスをクリック（配置）
            # 最初に見つかった未配置の駒を配置
            unplaced = self.board.get_unplaced_pieces(self.my_player)
            if unplaced:
                piece_type = unplaced[0].piece_type
                self.place_piece(piece_type, x, y)
                
    def handle_game_board_click(self, pos):
        """ゲーム画面での盤面クリック"""
        if self.current_player != self.my_player:
            return  # 自分のターンではない
            
        x, y = pos
        piece = self.board.get_piece_at(x, y)
        
        if self.ui.selected_piece is None:
            # 駒選択
            if piece is not None and piece.player == self.my_player and piece.is_movable:
                valid_moves = piece.get_valid_moves(self.board)
                if valid_moves:
                    self.ui.set_selected_piece((x, y), valid_moves)
        else:
            # 移動実行
            from_x, from_y = self.ui.selected_piece
            if (x, y) in self.ui.valid_moves:
                self.move_piece(from_x, from_y, x, y)
            else:
                # 選択解除または別の駒選択
                if piece is not None and piece.player == self.my_player and piece.is_movable:
                    valid_moves = piece.get_valid_moves(self.board)
                    if valid_moves:
                        self.ui.set_selected_piece((x, y), valid_moves)
                else:
                    self.ui.set_selected_piece(None, [])
                    
    def host_game(self):
        """ゲームをホスト"""
        try:
            from game_server import GunjinServer
            
            # サーバー開始
            self.server = GunjinServer()
            server_thread = threading.Thread(target=self._run_server)
            server_thread.daemon = True
            server_thread.start()
            
            time.sleep(2.0)  # サーバー開始待ち
            
            # 自分自身に接続
            if self.connect_to_server(self.server_host, self.server_port):
                pass  # 接続成功はhandle_connection_acceptedで処理
            else:
                self.ui.show_message("サーバーの開始に失敗しました", "エラー")
        except Exception as e:
            print(f"ホストエラー: {e}")
            self.ui.show_message("サーバーの開始に失敗しました", "エラー")
            
    def _run_server(self):
        """サーバー実行（スレッド内）"""
        try:
            self.server.start()
        except Exception as e:
            print(f"サーバー実行エラー: {e}")
            
    def join_game(self):
        """ゲームに参加"""
        # インスタンス変数のサーバー設定を使用
        host = self.server_host
        port = self.server_port
        
        print(f"サーバーに接続中: {host}:{port}")
        
        if self.connect_to_server(host, port):
            pass  # 接続成功は handle_connection_accepted で処理
        else:
            self.ui.show_message(f"サーバー {host}:{port} に接続できませんでした", "エラー")
            
    def place_piece(self, piece_type, x, y):
        """駒配置リクエスト"""
        request = {
            "type": MSG_SETUP_REQUEST,
            "data": {
                "action": "place",
                "piece_type": piece_type,
                "position": {"x": x, "y": y}
            }
        }
        self.network.send_message(request)
        
    def remove_piece(self, x, y):
        """駒除去リクエスト"""
        request = {
            "type": MSG_SETUP_REQUEST,
            "data": {
                "action": "remove",
                "position": {"x": x, "y": y}
            }
        }
        self.network.send_message(request)
        
    def auto_place_pieces(self):
        """自動配置リクエスト"""
        print(f"プレイヤー{self.my_player}: 自動配置ボタンがクリックされました")
        request = {
            "type": MSG_SETUP_REQUEST,
            "data": {
                "action": "auto"
            }
        }
        print(f"自動配置リクエスト送信: {request}")
        self.network.send_message(request)
        
    def complete_setup(self):
        """配置完了リクエスト"""
        request = {
            "type": MSG_SETUP_REQUEST,
            "data": {
                "action": "complete"
            }
        }
        self.network.send_message(request)
        
    def move_piece(self, from_x, from_y, to_x, to_y):
        """移動リクエスト"""
        request = {
            "type": MSG_MOVE_REQUEST,
            "data": {
                "from": {"x": from_x, "y": from_y},
                "to": {"x": to_x, "y": to_y}
            }
        }
        self.network.send_message(request)
        
        # 選択解除
        self.ui.set_selected_piece(None, [])
        
    # ネットワークメッセージハンドラ
    
    def handle_connection_accepted(self, message):
        """接続受諾処理"""
        data = message.get("data", {})
        self.my_player = data.get("player_id")
        
        print(f"プレイヤーID設定: {self.my_player} (Client向け)")
        
        self.ui.set_player_info(self.my_player)
        connection_msg = data.get("message", "接続しました")
        print(f"接続成功: {connection_msg}")
        
        # ゲーム状態に応じて追加メッセージを表示
        game_state = data.get("game_state", GAME_STATE_WAITING)
        if game_state == GAME_STATE_WAITING:
            print("他のプレイヤーの接続を待機中...")
        
    def handle_setup_update(self, message):
        """配置更新処理"""
        data = message.get("data", {})
        
        # ローカル盤面を更新
        self.update_local_board(data.get("visible_positions", []))
        
        # UI更新
        self.ui.set_remaining_pieces(data.get("remaining_pieces", {}))
        
        # 画面切り替え
        if self.ui.current_screen != "setup":
            self.ui.set_screen("setup")
            
    def handle_game_update(self, message):
        """ゲーム更新処理"""
        data = message.get("data", {})
        
        # ローカル盤面を更新
        self.update_local_board(data.get("board_state", []))
        
        # ゲーム情報更新
        self.current_player = data.get("current_player", PLAYER1)
        self.ui.set_game_info(self.current_player, self.game_state)
        
        # 画面切り替え
        if self.ui.current_screen != "game":
            self.ui.set_screen("game")
            
    def handle_battle_result(self, message):
        """戦闘結果処理"""
        data = message.get("data", {})
        
        # 戦闘アニメーション表示（簡易版）
        position = data.get("position", {})
        result = data.get("result")
        
        result_text = ""
        if result == BATTLE_WIN:
            result_text = "攻撃側勝利"
        elif result == BATTLE_LOSE:
            result_text = "攻撃側敗北"
        else:
            result_text = "相討ち"
            
        print(f"戦闘発生: {result_text}")
        
    def handle_game_state(self, message):
        """ゲーム状態更新処理"""
        data = message.get("data", {})
        
        # ゲーム状態を更新
        self.game_state = data.get("state", GAME_STATE_WAITING)
        self.current_player = data.get("current_player", PLAYER1)
        
        # 盤面データがあれば更新
        board_data = data.get("board_data")
        if board_data:
            self.ui.update_board_data(board_data)
        
        # ゲーム状態に応じた画面遷移
        if self.game_state == GAME_STATE_SETUP:
            self.ui.set_screen("setup")
        elif self.game_state == GAME_STATE_PLAYING:
            self.ui.set_screen("game")
        
        # 勝利判定
        winner = data.get("winner")
        if winner is not None:
            win_reason = data.get("win_reason", "")
            if winner == self.my_player:
                print(f"勝利！ ({win_reason})")
            else:
                print(f"敗北... ({win_reason})")
            self.ui.set_screen("menu")
            
        # UI更新
        self.ui.set_game_info(self.current_player, self.game_state)
        
    def handle_error(self, message):
        """エラー処理"""
        data = message.get("data", {})
        error_message = data.get("message", "不明なエラー")
        print(f"エラー: {error_message}")
        
    def handle_player_disconnected(self, message):
        """プレイヤー切断処理"""
        data = message.get("data", {})
        disconnect_message = data.get("message", "相手が切断しました")
        print(f"切断: {disconnect_message}")
        self.ui.set_screen("menu")
        
    def update_local_board(self, positions):
        """ローカル盤面を更新"""
        # 盤面をクリア
        self.board.reset()
        
        # 駒を配置
        for pos_data in positions:
            x = pos_data["x"]
            y = pos_data["y"]
            player = pos_data["player"]
            piece_type = pos_data.get("piece_type")
            
            if piece_type is not None:
                # 自分の駒（種類が分かる）
                from pieces import Piece
                piece = Piece(piece_type, player, x, y)
            else:
                # 相手の駒（種類不明、仮の駒を作成）
                from pieces import Piece
                piece = Piece(1, player, x, y)  # 仮の種類
                piece.is_hidden = True
                
            self.board.set_piece_at(x, y, piece)
            
        # UI用データ設定
        board_data = []
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                piece = self.board.get_piece_at(x, y)
                if piece is not None:
                    board_data.append({
                        "x": x, "y": y,
                        "player": piece.player,
                        "piece_type": piece.piece_type if not getattr(piece, 'is_hidden', False) else None
                    })
                    
        self.ui.set_board_state(board_data)


def main():
    """クライアントメイン関数"""
    # デフォルトの接続先を自動決定
    default_server = get_local_ip()
    
    parser = argparse.ArgumentParser(description='軍人将棋クライアント')
    parser.add_argument('--server', '-s', 
                       default=default_server,
                       help=f'接続先サーバーのIPアドレス (デフォルト: {default_server})')
    parser.add_argument('--port', '-p', 
                       type=int,
                       default=DEFAULT_PORT,
                       help=f'接続先サーバーのポート番号 (デフォルト: {DEFAULT_PORT})')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("軍人将棋 LAN対戦版 - クライアント")
    print("=" * 60)
    print(f"接続先サーバー: {args.server}:{args.port}")
    if args.server == default_server:
        print("(自動検出された自マシンのIPアドレスに接続)")
    print("=" * 60)
    
    client = GunjinClient(args.server, args.port)
    
    if not client.initialize():
        print("クライアント初期化に失敗しました")
        return
        
    try:
        client.run()
    except KeyboardInterrupt:
        print("\nクライアントを終了します...")
    finally:
        client.cleanup()


if __name__ == "__main__":
    main()
