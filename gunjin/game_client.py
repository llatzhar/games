"""
メインゲームクライアント
"""

import pygame
import sys
import threading
import time
from game_board import GameBoard
from network import NetworkManager, GameProtocol
from ui import UI
from constants import *

class GameClient:
    """ゲームクライアントクラス"""
    
    def __init__(self):
        pygame.init()
        self.game_board = GameBoard()
        self.network = None
        self.ui = UI()
        self.running = True
        self.player_number = PLAYER_1
        self.is_host = False
        self.clock = pygame.time.Clock()
        self.game_state = GAME_STATE_MENU  # ゲーム状態を初期化
        self.game_state = GAME_STATE_MENU
        
    def run(self):
        """メインループ"""
        while self.running:
            events, quit_requested = self.ui.handle_events()
            if quit_requested:
                break
            
            self.handle_events(events)
            self.update()
            self.draw()
            self.clock.tick(60)
        
        self.cleanup()
    
    def handle_events(self, events):
        """イベントを処理"""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_mouse_click(event.pos)
    
    def handle_mouse_click(self, pos):
        """マウスクリックを処理"""
        if self.game_state == GAME_STATE_MENU:
            self.handle_menu_click(pos)
        elif self.game_state == GAME_STATE_SETUP:
            self.handle_setup_click(pos)
        elif self.game_state == GAME_STATE_PLAYING:
            self.handle_game_click(pos)
    
    def handle_menu_click(self, pos):
        """メニューでのクリックを処理"""
        button = self.ui.check_button_click(pos)
        
        if button == "host":
            self.start_host()
        elif button == "join":
            self.join_game()
        elif button == "exit":
            self.running = False
    
    def handle_setup_click(self, pos):
        """セットアップでのクリックを処理"""
        button = self.ui.check_button_click(pos)
        
        if button == "auto_setup":
            self.game_board.auto_setup(self.player_number)
        elif button == "setup_complete":
            self.complete_setup()
    
    def handle_game_click(self, pos):
        """ゲーム中のクリックを処理"""
        print(f"ゲームクリック: pos={pos}, game_state={self.game_state}")
        x, y = self.ui.screen_to_board_pos(pos[0], pos[1])
        print(f"盤面座標: ({x}, {y})")
        if x is not None and y is not None:
            self.handle_piece_interaction(x, y)
    
    def handle_piece_interaction(self, x, y):
        """駒との相互作用を処理"""
        if self.game_board.current_player != self.player_number:
            return
        
        if self.game_board.selected_piece is None:
            # 駒を選択
            piece = self.game_board.get_piece_at(x, y)
            if piece and piece.player == self.player_number:
                success = self.game_board.select_piece(x, y)
        else:
            # 移動またはキャンセル
            if (x, y) in self.game_board.valid_moves:
                self.move_piece(self.game_board.selected_pos, (x, y))
            else:
                self.game_board.selected_piece = None
                self.game_board.selected_pos = None
                self.game_board.valid_moves = []
    
    def start_host(self):
        """ホストとしてゲームを開始"""
        self.is_host = True
        self.player_number = PLAYER_1
        self.network = NetworkManager(is_host=True)
        
        if self.network.start_server():
            self.game_state = GAME_STATE_WAITING
            self.setup_network_handlers()
        else:
            print("サーバー開始に失敗しました")
            self.game_state = GAME_STATE_MENU
    
    def join_game(self):
        """ゲームに参加"""
        self.is_host = False
        self.player_number = PLAYER_2
        self.network = NetworkManager(is_host=False)
        
        if self.network.connect_to_server("localhost"):
            self.game_state = GAME_STATE_SETUP
            self.setup_network_handlers()
        else:
            print("サーバーへの接続に失敗しました")
            self.game_state = GAME_STATE_MENU
    
    def setup_network_handlers(self):
        """ネットワークハンドラーを設定"""
        if not self.network:
            return
        
        self.network.register_handler('setup_complete', self.handle_setup_complete_msg)
        self.network.register_handler('setup_positions', self.handle_setup_positions_msg)
        self.network.register_handler('move', self.handle_move_msg)
        self.network.register_handler('battle_result', self.handle_battle_result_msg)
        self.network.register_handler('game_start', self.handle_game_start_msg)
        self.network.register_handler('reveal_piece', self.handle_reveal_piece_msg)
    
    def complete_setup(self):
        """セットアップを完了"""
        self.game_board.setup_complete[self.player_number] = True
        
        if self.network:
            # 自分の駒の位置情報を収集（相手には位置のみ送信）
            positions = []
            for y in range(6):
                for x in range(8):
                    piece = self.game_board.get_piece_at(x, y)
                    if piece and piece.player == self.player_number:
                        positions.append({'x': x, 'y': y})
            
            # 駒の位置情報を送信
            pos_message = GameProtocol.setup_positions(self.player_number, positions)
            self.network.send_message(pos_message)
            
            # セットアップ完了メッセージを送信
            message = GameProtocol.setup_complete(self.player_number)
            self.network.send_message(message)
        
        if self.game_board.is_setup_complete():
            self.start_game()
        else:
            self.game_state = GAME_STATE_WAITING
    
    def start_game(self):
        """ゲームを開始"""
        print("ゲームを開始します")
        self.game_state = GAME_STATE_PLAYING
        self.game_board.game_state = GAME_STATE_PLAYING
        print(f"ゲーム状態を {GAME_STATE_PLAYING} に設定")
        
        if self.is_host and self.network:
            message = GameProtocol.game_start()
            self.network.send_message(message)
    
    def move_piece(self, from_pos, to_pos):
        """駒を移動"""
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        print(f"自分の移動を実行: ({from_x},{from_y}) → ({to_x},{to_y})")
        
        # 移動先に相手の駒があるかチェック（戦闘が発生するか）
        target_piece = self.game_board.get_piece_at(to_x, to_y)
        moving_piece = self.game_board.get_piece_at(from_x, from_y)
        
        # 戦闘が発生する場合のための駒の種類を取得
        piece_type_for_battle = None
        battle_will_occur = False
        
        if target_piece and target_piece.player != self.player_number and moving_piece:
            piece_type_for_battle = moving_piece.piece_type
            battle_will_occur = True
            print(f"戦闘が発生します - 自分の駒: {moving_piece.get_name()}")
            
            # 移動メッセージを先に送信
            move_msg = GameProtocol.move(from_pos, to_pos, self.player_number, piece_type_for_battle)
            print(f"移動メッセージを送信: プレイヤー{self.player_number} (駒の種類: {piece_type_for_battle})")
            if self.network:
                self.network.send_message(move_msg)
            
            # 相手の駒の種類開示を待機
            print("相手の駒の種類開示を待機中...")
            if self._wait_for_piece_reveal(to_x, to_y):
                print("駒の種類開示を受信しました")
            else:
                print("駒の種類開示のタイムアウト - 戦闘をスキップします")
                return
        
        success, message = self.game_board.move_piece(from_x, from_y, to_x, to_y)
        print(f"移動結果: success={success}, message={message}")
        
        if success and self.network and not battle_will_occur:
            # 戦闘が発生しない場合のみ、ここで移動メッセージを送信
            move_msg = GameProtocol.move(from_pos, to_pos, self.player_number)
            print(f"移動メッセージを送信: プレイヤー{self.player_number}")
            self.network.send_message(move_msg)
        elif not success:
            print(f"移動失敗: {message}")
        
        if not self.network:
            print("ネットワークが接続されていません")
    
    def _wait_for_piece_reveal(self, x, y, timeout=2.0):
        """駒の種類開示を待機（タイムアウト付き）"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.network:
                messages = self.network.get_messages()
                for message in messages:
                    if (message.get('type') == 'reveal_piece' and 
                        message.get('position') == [x, y]):
                        # 即座に駒の種類を更新
                        piece_type = message.get('piece_type')
                        player = message.get('player')
                        if piece_type and player != self.player_number:
                            piece = self.game_board.get_piece_at(x, y)
                            if piece:
                                print(f"駒の種類開示を受信: ({x},{y}) {piece_type}")
                                piece.piece_type = piece_type
                                return True
            time.sleep(0.1)
        
        return False
    
    def handle_setup_complete_msg(self, message):
        """セットアップ完了メッセージを処理"""
        player = message.get('player')
        if player:
            self.game_board.setup_complete[player] = True
        
        if self.game_board.is_setup_complete():
            self.start_game()
    
    def handle_setup_positions_msg(self, message):
        """セットアップ位置情報メッセージを処理"""
        player = message.get('player')
        positions = message.get('positions', [])
        
        # 相手の駒の位置を盤面に配置（種類は不明のまま）
        if player != self.player_number:
            from pieces import Piece
            for pos in positions:
                x, y = pos['x'], pos['y']
                # 相手の駒は種類不明として配置（"?"として表示される）
                piece = Piece("?", player, x, y)
                piece.is_hidden = True  # 隠蔽フラグ
                self.game_board.set_piece_at(x, y, piece)
    
    def handle_move_msg(self, message):
        """移動メッセージを処理"""
        from_pos = message.get('from')
        to_pos = message.get('to')
        player = message.get('player')
        piece_type = message.get('piece_type')  # 戦闘時の駒の種類情報
        
        print(f"移動メッセージ受信: プレイヤー{player} ({from_pos} → {to_pos})" + 
              (f" 駒の種類: {piece_type}" if piece_type else ""))
        
        if player != self.player_number and from_pos and to_pos:
            from_x, from_y = from_pos
            to_x, to_y = to_pos
            
            # 移動先に自分の駒があるかチェック（戦闘が発生するか）
            target_piece = self.game_board.get_piece_at(to_x, to_y)
            moving_piece = self.game_board.get_piece_at(from_x, from_y)
            
            if target_piece and target_piece.player == self.player_number and piece_type:
                # 戦闘が発生する場合、相手の駒の種類を設定
                if moving_piece:
                    print(f"戦闘発生 - 相手の駒の種類を設定: {piece_type}")
                    moving_piece.piece_type = piece_type
                
                # 自分の駒の種類も相手に送信
                reveal_msg = GameProtocol.reveal_piece((to_x, to_y), target_piece.piece_type, self.player_number)
                if self.network:
                    self.network.send_message(reveal_msg)
                    print(f"自分の駒の種類を開示: {target_piece.get_name()}")
            
            print(f"相手の移動を実行: ({from_x},{from_y}) → ({to_x},{to_y})")
            success, message_result = self.game_board.move_piece(from_x, from_y, to_x, to_y)
            print(f"相手の移動結果: success={success}, message={message_result}")
        else:
            print(f"移動メッセージをスキップ: player={player}, self.player_number={self.player_number}")
    
    def handle_battle_result_msg(self, message):
        """戦闘結果メッセージを処理"""
        result = message.get('result')
        print(f"戦闘結果: {result}")
    
    def handle_game_start_msg(self, message):
        """ゲーム開始メッセージを処理"""
        print("ゲーム開始メッセージを受信")
        self.game_state = GAME_STATE_PLAYING
        self.game_board.game_state = GAME_STATE_PLAYING
        print(f"ゲーム状態を {GAME_STATE_PLAYING} に設定")
    
    def handle_reveal_piece_msg(self, message):
        """駒の種類開示メッセージを処理"""
        position = message.get('position')
        piece_type = message.get('piece_type')
        player = message.get('player')
        
        if position and piece_type and player != self.player_number:
            x, y = position
            piece = self.game_board.get_piece_at(x, y)
            if piece:
                print(f"相手の駒の種類が判明: ({x},{y}) {piece_type}")
                piece.piece_type = piece_type
                # 表示はまだ隠蔽状態のまま（戦闘時のみ明かす）
    
    def update(self):
        """ゲーム状態を更新"""
        if self.network:
            messages = self.network.get_messages()
            if messages:
                print(f"メッセージを{len(messages)}件受信")
                for message in messages:
                    print(f"メッセージ内容: {message}")
        
        if self.game_state == GAME_STATE_WAITING:
            if self.is_host and self.network and self.network.is_connected():
                self.game_state = GAME_STATE_SETUP
        
        # 勝利条件チェックを一時無効化（デバッグ用）
        # if self.game_state == GAME_STATE_PLAYING and self.game_board.check_victory():
        #     self.game_state = GAME_STATE_GAME_OVER
    
    def draw(self):
        """画面を描画"""
        # デバッグ：ゲーム状態を表示
        if hasattr(self, '_last_state') and self._last_state != self.game_state:
            print(f"ゲーム状態変更: {self._last_state} -> {self.game_state}")
        self._last_state = self.game_state
        
        if self.game_state == GAME_STATE_MENU:
            self.ui.draw_menu()
        elif self.game_state == GAME_STATE_WAITING:
            self.ui.screen.fill(LIGHT_GRAY)
            text = "プレイヤーの接続を待っています..." if self.is_host else "サーバーに接続中..."
            surface = self.ui.font_medium.render(text, True, BLACK)
            rect = surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
            self.ui.screen.blit(surface, rect)
        elif self.game_state == GAME_STATE_SETUP:
            self.ui.draw_board(self.game_board, self.player_number)
            self.ui.draw_setup_screen()
        elif self.game_state == GAME_STATE_PLAYING:
            self.ui.draw_board(self.game_board, self.player_number)
            self.ui.draw_ui_elements("playing", self.game_board.current_player, self.player_number)
        elif self.game_state == GAME_STATE_GAME_OVER:
            self.ui.draw_board(self.game_board, self.player_number)
            text = "ゲーム終了"
            surface = self.ui.font_large.render(text, True, RED)
            rect = surface.get_rect(center=(WINDOW_WIDTH//2, 50))
            self.ui.screen.blit(surface, rect)
        
        self.ui.update_display()
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.network:
            self.network.disconnect()
        pygame.quit()
