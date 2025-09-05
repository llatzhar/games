# -*- coding: utf-8 -*-
"""
軍人将棋 - ユーザーインターフェース
"""

import pygame
import sys
from constants import *
from pieces import get_piece_display_name, get_piece_display_color

class GameUI:
    """ゲームのUI管理クラス"""
    
    def __init__(self, width=1024, height=768):
        self.width = width
        self.height = height
        self.screen = None
        self.clock = None
        self.font = None
        self.title_font = None
        self.piece_font = None
        
        # UI状態
        self.current_screen = "menu"  # menu, setup, game
        self.selected_piece = None
        self.valid_moves = []
        self.my_player = None
        self.board_data = None  # サーバーから受信した盤面データ
        
        # イベントハンドラ
        self.event_handlers = {}
        
    def initialize(self):
        """UIを初期化"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("軍人将棋 LAN対戦版")
        self.clock = pygame.time.Clock()
        
        # フォント初期化
        self.font = pygame.font.SysFont("msgothic", UI_FONT_SIZE)
        self.title_font = pygame.font.SysFont("msgothic", TITLE_FONT_SIZE)
        self.piece_font = pygame.font.SysFont("msgothic", PIECE_FONT_SIZE)
        
        print("UI初期化完了")
        return True
        
    def register_event_handler(self, event_type, handler):
        """イベントハンドラを登録"""
        self.event_handlers[event_type] = handler
        
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            # 登録されたハンドラを呼び出し
            for event_type, handler in self.event_handlers.items():
                if event.type == event_type:
                    handler(event)
                    
        return True
        
    def update_display(self):
        """画面を更新"""
        if self.current_screen == "menu":
            self.draw_menu_screen()
        elif self.current_screen == "setup":
            self.draw_setup_screen()
        elif self.current_screen == "game":
            self.draw_game_screen()
            
        pygame.display.flip()
        self.clock.tick(60)
        
    def draw_menu_screen(self):
        """メニュー画面を描画"""
        self.screen.fill(COLOR_WHITE)
        
        # タイトル
        title_text = self.title_font.render("軍人将棋 LAN対戦版", True, COLOR_BLACK)
        title_rect = title_text.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # メニューボタン
        button_width = 200
        button_height = 50
        button_spacing = 20
        button_x = (self.width - button_width) // 2
        start_y = 200
        
        buttons = [
            ("ホストゲーム", "host_game"),
            ("ゲームに参加", "join_game"),
            ("終了", "quit")
        ]
        
        for i, (text, action) in enumerate(buttons):
            button_y = start_y + i * (button_height + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            # ボタンの背景
            pygame.draw.rect(self.screen, COLOR_LIGHT_GRAY, button_rect)
            pygame.draw.rect(self.screen, COLOR_BLACK, button_rect, 2)
            
            # ボタンのテキスト
            button_text = self.font.render(text, True, COLOR_BLACK)
            text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, text_rect)
            
            # クリック判定用に矩形を保存
            setattr(self, f"{action}_rect", button_rect)
            
    def draw_setup_screen(self):
        """配置画面を描画"""
        self.screen.fill(COLOR_WHITE)
        
        # タイトル
        title_text = self.title_font.render("駒配置", True, COLOR_BLACK)
        title_rect = title_text.get_rect(center=(self.width // 2, 30))
        self.screen.blit(title_text, title_rect)
        
        # 盤面を描画
        self.draw_board()
        
        # 駒を描画
        if hasattr(self, 'board_state'):
            board_start_x = BOARD_MARGIN
            board_start_y = 80
            
            for piece_data in self.board_state:
                # 仮の駒オブジェクトを作成して描画
                class TempPiece:
                    def __init__(self, data):
                        self.x = data["x"]
                        self.y = data["y"]
                        self.player = data["player"]
                        self.piece_type = data.get("piece_type", 1)
                        
                temp_piece = TempPiece(piece_data)
                self.draw_piece(temp_piece, board_start_x, board_start_y)
        
        # 配置パネルを描画
        self.draw_setup_panel()
        
    def draw_game_screen(self):
        """ゲーム画面を描画"""
        self.screen.fill(COLOR_WHITE)
        
        # ゲーム情報表示
        self.draw_game_info()
        
        # 盤面を描画
        self.draw_board()
        
        # 駒を描画
        if hasattr(self, 'board_state'):
            board_start_x = BOARD_MARGIN
            board_start_y = 80
            
            for piece_data in self.board_state:
                # 仮の駒オブジェクトを作成して描画
                class TempPiece:
                    def __init__(self, data):
                        self.x = data["x"]
                        self.y = data["y"]
                        self.player = data["player"]
                        self.piece_type = data.get("piece_type", 1)
                        
                temp_piece = TempPiece(piece_data)
                highlight = (self.selected_piece is not None and 
                           self.selected_piece == (piece_data["x"], piece_data["y"]))
                self.draw_piece(temp_piece, board_start_x, board_start_y, highlight)
        
    def draw_board(self):
        """ゲーム盤面を描画"""
        board_start_x = BOARD_MARGIN
        board_start_y = 80
        
        # 盤面の背景
        board_width = BOARD_WIDTH * CELL_SIZE
        board_height = BOARD_HEIGHT * CELL_SIZE + NEUTRAL_ZONE_HEIGHT * CELL_SIZE
        board_rect = pygame.Rect(board_start_x, board_start_y, board_width, board_height)
        pygame.draw.rect(self.screen, COLOR_BROWN, board_rect)
        
        # グリッド線を描画
        for x in range(BOARD_WIDTH + 1):
            start_pos = (board_start_x + x * CELL_SIZE, board_start_y)
            end_pos = (board_start_x + x * CELL_SIZE, board_start_y + board_height)
            pygame.draw.line(self.screen, COLOR_BLACK, start_pos, end_pos)
            
        for y in range(BOARD_HEIGHT + 1 + 1): # 侵入不可領域分+1
            start_pos = (board_start_x, board_start_y + y * CELL_SIZE)
            end_pos = (board_start_x + board_width, board_start_y + y * CELL_SIZE)
            pygame.draw.line(self.screen, COLOR_BLACK, start_pos, end_pos)
            
        # 司令部をハイライト
        self.draw_headquarters(board_start_x, board_start_y)
        
        # 侵入不可領域を表示
        self.draw_neutral_zone(board_start_x, board_start_y)
        
        # 移動可能位置を表示
        self.draw_valid_moves(board_start_x, board_start_y)
        
    def draw_headquarters(self, board_x, board_y):
        """司令部を描画"""
        # プレイヤー1司令部（赤）
        for hq_x, hq_y in PLAYER1_HEADQUARTERS:
            cell_x = board_x + hq_x * CELL_SIZE
            cell_y = board_y + (hq_y + NEUTRAL_ZONE_HEIGHT) * CELL_SIZE
            cell_rect = pygame.Rect(cell_x + 2, cell_y + 2, CELL_SIZE * 2 - 3, CELL_SIZE - 4)
            pygame.draw.rect(self.screen, (255, 200, 200), cell_rect)
            
        # プレイヤー2司令部（青）
        for hq_x, hq_y in PLAYER2_HEADQUARTERS:
            cell_x = board_x + hq_x * CELL_SIZE
            cell_y = board_y + hq_y * CELL_SIZE
            cell_rect = pygame.Rect(cell_x + 2, cell_y + 2, CELL_SIZE * 2 - 3, CELL_SIZE - 4)
            pygame.draw.rect(self.screen, (200, 200, 255), cell_rect)
            
    def draw_neutral_zone(self, board_x, board_y):
        """侵入不可領域を描画"""
        # 中立地帯
        for x in range(BOARD_WIDTH):
            if (x, NEUTRAL_ZONE_Y) not in BRIDGE_POSITIONS:
                cell_x = board_x + x * CELL_SIZE
                cell_y = board_y + NEUTRAL_ZONE_Y * CELL_SIZE
                cell_rect = pygame.Rect(cell_x + 2, cell_y + 2, CELL_SIZE - 4, CELL_SIZE - 4)
                pygame.draw.rect(self.screen, COLOR_GRAY, cell_rect)
                
        # 突入口（橋）
        for bridge_x, bridge_y in BRIDGE_POSITIONS:
            cell_x = board_x + bridge_x * CELL_SIZE
            cell_y = board_y + bridge_y * CELL_SIZE
            cell_rect = pygame.Rect(cell_x + 2, cell_y + 2, CELL_SIZE - 4, CELL_SIZE - 4)
            pygame.draw.rect(self.screen, COLOR_YELLOW, cell_rect)
            
    def draw_valid_moves(self, board_x, board_y):
        """移動可能位置を描画"""
        for move_x, move_y in self.valid_moves:
            cell_x = board_x + move_x * CELL_SIZE
            cell_y = board_y + move_y * CELL_SIZE
            cell_rect = pygame.Rect(cell_x + 4, cell_y + 4, CELL_SIZE - 8, CELL_SIZE - 8)
            pygame.draw.rect(self.screen, VALID_MOVE_COLOR, cell_rect)
            
    def draw_piece(self, piece, board_x, board_y, highlight=False):
        """駒を描画"""
        if piece.x is None or piece.y is None:
            return
            
        cell_x = board_x + piece.x * CELL_SIZE
        if piece.y < 3:
            cell_y = board_y + piece.y * CELL_SIZE
        else:
            cell_y = board_y + (piece.y + NEUTRAL_ZONE_HEIGHT) * CELL_SIZE 
        
        # 駒の背景円
        center_x = cell_x + CELL_SIZE // 2
        center_y = cell_y + CELL_SIZE // 2
        radius = CELL_SIZE // 3
        
        # ハイライト
        if highlight:
            pygame.draw.circle(self.screen, SELECTED_COLOR, (center_x, center_y), radius + 3)
            
        # 駒の色
        piece_color = get_piece_display_color(piece.piece_type, piece.player, self.my_player)
        pygame.draw.circle(self.screen, piece_color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, COLOR_BLACK, (center_x, center_y), radius, 2)
        
        # 駒の名前
        piece_name = get_piece_display_name(piece.piece_type, piece.player, self.my_player)
        if len(piece_name) > 2:
            # 長い名前は縮小
            piece_name = piece_name[:2]
            
        text = self.piece_font.render(piece_name, True, COLOR_WHITE)
        text_rect = text.get_rect(center=(center_x, center_y))
        self.screen.blit(text, text_rect)
        
    def draw_setup_panel(self):
        """配置パネルを描画"""
        panel_x = BOARD_MARGIN + BOARD_WIDTH * CELL_SIZE + 20
        panel_y = 80
        panel_width = 200
        
        # パネル背景
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, 400)
        pygame.draw.rect(self.screen, COLOR_LIGHT_GRAY, panel_rect)
        pygame.draw.rect(self.screen, COLOR_BLACK, panel_rect, 2)
        
        # タイトル
        title_text = self.font.render("残り駒", True, COLOR_BLACK)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))
        
        # 駒リスト（残り数が0でない駒のみ表示）
        y_offset = 40
        if hasattr(self, 'remaining_pieces') and self.remaining_pieces:
            for piece_type, count in self.remaining_pieces.items():
                try:
                    if count > 0:
                        # piece_typeが文字列の場合は整数に変換
                        piece_type_int = int(piece_type) if isinstance(piece_type, str) else piece_type
                        if piece_type_int in PIECE_TYPES:
                            piece_name = PIECE_TYPES[piece_type_int]["name"]
                            piece_text = f"{piece_name}: {count}"
                            text = self.font.render(piece_text, True, COLOR_BLACK)
                            self.screen.blit(text, (panel_x + 10, panel_y + y_offset))
                            y_offset += 25
                except (ValueError, KeyError, TypeError):
                    # 不正な駒タイプはスキップ
                    print(f"警告: 不正な駒タイプをスキップしました - {piece_type}: {count}")
                    continue
        
        # 操作ボタン
        button_y = panel_y + 300
        button_width = panel_width - 20
        button_height = 30
        
        buttons = [
            ("自動配置", "auto_place"),
            ("配置完了", "complete_setup")
        ]
        
        for i, (text, action) in enumerate(buttons):
            button_rect = pygame.Rect(
                panel_x + 10,
                button_y + i * 40,
                button_width,
                button_height
            )
            
            pygame.draw.rect(self.screen, COLOR_WHITE, button_rect)
            pygame.draw.rect(self.screen, COLOR_BLACK, button_rect, 2)
            
            button_text = self.font.render(text, True, COLOR_BLACK)
            text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, text_rect)
            
            # クリック判定用
            setattr(self, f"{action}_rect", button_rect)
            
    def draw_game_info(self):
        """ゲーム情報を描画"""
        info_y = 10
        
        # 現在のプレイヤー
        if hasattr(self, 'current_player'):
            player_text = f"現在のターン: プレイヤー{self.current_player}"
            if self.current_player == self.my_player:
                player_text += " (あなた)"
            text = self.font.render(player_text, True, COLOR_BLACK)
            self.screen.blit(text, (10, info_y))
            
        # ゲーム状態
        if hasattr(self, 'game_state'):
            state_text = f"状態: {self.game_state}"
            text = self.font.render(state_text, True, COLOR_BLACK)
            self.screen.blit(text, (10, info_y + 25))
            
    def get_board_position(self, mouse_pos):
        """マウス位置から盤面座標を取得"""
        mouse_x, mouse_y = mouse_pos
        board_start_x = BOARD_MARGIN
        board_start_y = 80
        
        if (board_start_x <= mouse_x < board_start_x + BOARD_WIDTH * CELL_SIZE and
            board_start_y <= mouse_y < board_start_y + BOARD_HEIGHT * CELL_SIZE):
            
            board_x = (mouse_x - board_start_x) // CELL_SIZE
            board_y = (mouse_y - board_start_y) // CELL_SIZE
            return (board_x, board_y)
            
        return None
        
    def is_button_clicked(self, button_name, mouse_pos):
        """ボタンがクリックされたかチェック"""
        button_rect = getattr(self, f"{button_name}_rect", None)
        if button_rect is None:
            return False
        return button_rect.collidepoint(mouse_pos)
        
    def set_screen(self, screen_name):
        """画面を切り替え"""
        self.current_screen = screen_name
        self.selected_piece = None
        self.valid_moves = []
        
    def set_board_state(self, board_state):
        """盤面状態を設定"""
        self.board_state = board_state
        
    def set_remaining_pieces(self, remaining_pieces):
        """残り駒数を設定"""
        # キーを整数に正規化
        normalized_pieces = {}
        for piece_type, count in remaining_pieces.items():
            try:
                piece_type_int = int(piece_type)
                if piece_type_int in PIECE_TYPES:
                    normalized_pieces[piece_type_int] = count
            except (ValueError, TypeError):
                continue
        self.remaining_pieces = normalized_pieces
        
    def set_player_info(self, player_id):
        """プレイヤー情報を設定"""
        self.my_player = player_id
        
    def set_game_info(self, current_player, game_state):
        """ゲーム情報を設定"""
        self.current_player = current_player
        self.game_state = game_state
        
    def set_selected_piece(self, piece_pos, valid_moves):
        """選択中の駒を設定"""
        self.selected_piece = piece_pos
        self.valid_moves = valid_moves
        
    def show_message(self, message, title="メッセージ"):
        """メッセージダイアログを表示"""
        # 簡易メッセージ表示
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill(COLOR_BLACK)
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # メッセージボックス
        box_width = 400
        box_height = 150
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        
        pygame.draw.rect(self.screen, COLOR_WHITE, box_rect)
        pygame.draw.rect(self.screen, COLOR_BLACK, box_rect, 3)
        
        # タイトル
        title_text = self.font.render(title, True, COLOR_BLACK)
        title_rect = title_text.get_rect(center=(box_x + box_width // 2, box_y + 30))
        self.screen.blit(title_text, title_rect)
        
        # メッセージ
        message_text = self.font.render(message, True, COLOR_BLACK)
        message_rect = message_text.get_rect(center=(box_x + box_width // 2, box_y + 80))
        self.screen.blit(message_text, message_rect)
        
        pygame.display.flip()
        
        # キー入力待ち
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
                elif event.type == pygame.QUIT:
                    return False
        return True
    
    def update_board_data(self, board_data):
        """盤面データを更新"""
        self.board_data = board_data
        
    def cleanup(self):
        """UIリソースを解放"""
        pygame.quit()
