"""
pygame UI コンポーネント
"""

import pygame
import pygame.font
import sys
import os
from constants import *

class UI:
    """UIクラス"""
    
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        # 画面設定
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("軍人将棋 LAN対戦")
        
        # フォント設定
        self.font_small = pygame.font.Font(None, FONT_SIZE_SMALL)
        self.font_medium = pygame.font.Font(None, FONT_SIZE_MEDIUM)
        self.font_large = pygame.font.Font(None, FONT_SIZE_LARGE)
        
        # 日本語フォント
        try:
            self.font_japanese = pygame.font.SysFont('msgothic', FONT_SIZE_MEDIUM)
            self.font_japanese_small = pygame.font.SysFont('msgothic', FONT_SIZE_SMALL)
        except:
            self.font_japanese = self.font_medium
            self.font_japanese_small = self.font_small
        
        # ボタンリスト
        self.buttons = []
    
    def draw_board(self, game_board, player_view=PLAYER_1):
        """ゲーム盤面を描画"""
        self.screen.fill(LIGHT_GRAY)
        
        # 盤面背景
        pygame.draw.rect(self.screen, LIGHT_BROWN,
                        (BOARD_OFFSET_X - 5, BOARD_OFFSET_Y - 5,
                         BOARD_WIDTH * CELL_SIZE + 10, BOARD_HEIGHT * CELL_SIZE + 10))
        
        # セットアップエリアのハイライト
        setup_areas = {}
        if game_board.game_state == "setup":
            setup_areas[PLAYER_1] = set(game_board.get_setup_area(PLAYER_1))
            setup_areas[PLAYER_2] = set(game_board.get_setup_area(PLAYER_2))
        
        # マス目を描画
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                cell_x = BOARD_OFFSET_X + x * CELL_SIZE
                cell_y = BOARD_OFFSET_Y + y * CELL_SIZE
                
                # セル背景色
                is_light = (x + y) % 2 == 0
                color = LIGHT_BROWN if is_light else DARK_BROWN
                
                # セットアップエリアのハイライト
                if (x, y) in setup_areas.get(PLAYER_1, set()):
                    color = (200, 255, 200)  # 薄緑
                elif (x, y) in setup_areas.get(PLAYER_2, set()):
                    color = (255, 200, 200)  # 薄赤
                
                # 選択された駒のハイライト
                if game_board.selected_pos == (x, y):
                    color = YELLOW
                elif (x, y) in game_board.valid_moves:
                    color = GREEN
                
                pygame.draw.rect(self.screen, color,
                               (cell_x, cell_y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.screen, BLACK,
                               (cell_x, cell_y, CELL_SIZE, CELL_SIZE), 1)
                
                # 総司令部をハイライト
                if (x, y) in game_board.get_headquarters(PLAYER_1):
                    pygame.draw.rect(self.screen, RED,
                                   (cell_x + 2, cell_y + 2, CELL_SIZE - 4, CELL_SIZE - 4), 3)
                elif (x, y) in game_board.get_headquarters(PLAYER_2):
                    pygame.draw.rect(self.screen, RED,
                                   (cell_x + 2, cell_y + 2, CELL_SIZE - 4, CELL_SIZE - 4), 3)
                
                # 駒を描画
                piece = game_board.get_piece_at(x, y)
                if piece:
                    self._draw_piece(piece, cell_x, cell_y, player_view)
    
    def _draw_piece(self, piece, cell_x, cell_y, player_view):
        """駒を描画"""
        center_x = cell_x + CELL_SIZE // 2
        center_y = cell_y + CELL_SIZE // 2
        radius = CELL_SIZE // 3
        
        # 駒の円
        piece_color = WHITE if piece.player == PLAYER_1 else BLACK
        pygame.draw.circle(self.screen, piece_color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, BLACK, (center_x, center_y), radius, 2)
        
        # 駒のテキスト
        if piece.player == player_view:
            # 自分の駒は種類を表示
            text = piece.get_display_name()
            text_color = BLACK if piece.player == PLAYER_1 else WHITE
        else:
            # 相手の駒は「?」を表示
            text = "?"
            text_color = WHITE if piece.player == PLAYER_1 else BLACK
        
        text_surface = self.font_japanese_small.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(center_x, center_y))
        self.screen.blit(text_surface, text_rect)
    
    def screen_to_board_pos(self, screen_x, screen_y):
        """画面座標を盤面座標に変換"""
        if (BOARD_OFFSET_X <= screen_x <= BOARD_OFFSET_X + BOARD_WIDTH * CELL_SIZE and
            BOARD_OFFSET_Y <= screen_y <= BOARD_OFFSET_Y + BOARD_HEIGHT * CELL_SIZE):
            
            board_x = (screen_x - BOARD_OFFSET_X) // CELL_SIZE
            board_y = (screen_y - BOARD_OFFSET_Y) // CELL_SIZE
            return int(board_x), int(board_y)
        
        return None, None
    
    def draw_ui_elements(self, game_state, current_player, player_num):
        """UI要素を描画"""
        info_y = BOARD_OFFSET_Y + BOARD_HEIGHT * CELL_SIZE + 20
        
        # 現在のプレイヤー表示
        if game_state == "playing":
            if current_player == player_num:
                text = "あなたのターンです"
                color = GREEN
            else:
                text = "相手のターンです"
                color = RED
        else:
            text = f"ゲーム状態: {game_state}"
            color = BLACK
        
        text_surface = self.font_japanese.render(text, True, color)
        self.screen.blit(text_surface, (BOARD_OFFSET_X, info_y))
        
        # プレイヤー番号表示
        player_text = f"プレイヤー{player_num}"
        player_surface = self.font_japanese_small.render(player_text, True, BLACK)
        self.screen.blit(player_surface, (BOARD_OFFSET_X, info_y + 30))
    
    def draw_menu(self):
        """メニュー画面を描画"""
        self.screen.fill(LIGHT_GRAY)
        
        # タイトル
        title = "軍人将棋 LAN対戦"
        title_surface = self.font_japanese.render(title, True, BLACK)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title_surface, title_rect)
        
        # ボタンを描画
        self.buttons.clear()
        
        # ホストボタン
        host_button = self.create_button("ゲームを主催", WINDOW_WIDTH // 2, 200, 200, 50)
        self.buttons.append(("host", host_button))
        
        # 参加ボタン
        join_button = self.create_button("ゲームに参加", WINDOW_WIDTH // 2, 280, 200, 50)
        self.buttons.append(("join", join_button))
        
        # 終了ボタン
        exit_button = self.create_button("終了", WINDOW_WIDTH // 2, 360, 200, 50)
        self.buttons.append(("exit", exit_button))
    
    def create_button(self, text, x, y, width, height):
        """ボタンを作成"""
        button_rect = pygame.Rect(x - width//2, y - height//2, width, height)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        # ボタン背景
        color = GRAY if is_hover else LIGHT_GRAY
        pygame.draw.rect(self.screen, color, button_rect)
        pygame.draw.rect(self.screen, BLACK, button_rect, 2)
        
        # ボタンテキスト
        text_surface = self.font_japanese.render(text, True, BLACK)
        text_rect = text_surface.get_rect(center=button_rect.center)
        self.screen.blit(text_surface, text_rect)
        
        return button_rect
    
    def check_button_click(self, pos):
        """ボタンクリックをチェック"""
        for button_id, button_rect in self.buttons:
            if button_rect.collidepoint(pos):
                return button_id
        return None
    
    def draw_setup_screen(self):
        """セットアップ画面を描画"""
        # タイトル
        title = "駒の配置"
        title_surface = self.font_japanese.render(title, True, BLACK)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 30))
        self.screen.blit(title_surface, title_rect)
        
        # 自動配置ボタン
        auto_button = self.create_button("自動配置", WINDOW_WIDTH // 2, 500, 150, 40)
        self.buttons = [("auto_setup", auto_button)]
        
        # 完了ボタン
        complete_button = self.create_button("配置完了", WINDOW_WIDTH // 2, 560, 150, 40)
        self.buttons.append(("setup_complete", complete_button))
    
    def update_display(self):
        """画面を更新"""
        pygame.display.flip()
    
    def handle_events(self):
        """イベントを処理"""
        events = []
        for event in pygame.event.get():
            events.append(event)
            if event.type == pygame.QUIT:
                return events, True
        return events, False
