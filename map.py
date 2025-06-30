import pyxel
import math

# game.pyから定数をインポート
from game import screen_width, screen_height, char_width, char_height, Scene

class City:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x  # ワールド座標（ピクセル）
        self.y = y  # ワールド座標（ピクセル）
        self.size = 20  # Cityの表示サイズ
        
class Road:
    def __init__(self, city1, city2):
        self.city1 = city1
        self.city2 = city2

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = char_width
        self.height = char_height
        self.speed = 2
        self.target_x = None  # 移動目標X座標
        self.target_y = None  # 移動目標Y座標
        self.is_moving = False  # 移動中フラグ
        self.facing_right = True  # 向いている方向（True: 右, False: 左）

class MapScene(Scene):
    def __init__(self):
        self.click_x = -1  # クリック位置のX座標
        self.click_y = -1  # クリック位置のY座標
        self.click_timer = 0  # クリック座標表示時間
        self.selected_player = None  # 選択中のプレイヤー
        
        # カメラ位置（ビューの左上座標）
        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 4  # カメラの移動速度
        
        # マウスカーソルを表示
        pyxel.mouse(True)
        
        # 30x30のマップデータを生成
        self.map_width = 30
        self.map_height = 30
        self.map_data = self.generate_30x30_map()
        
        self.tile_size = 16
        
        # マップ全体のピクセルサイズ
        self.map_pixel_width = self.map_width * self.tile_size
        self.map_pixel_height = self.map_height * self.tile_size
        
        # Cityを定義（4つの街）
        self.cities = [
            City("Town A", 3 * self.tile_size, 3 * self.tile_size),      # 左上
            City("Town B", 25 * self.tile_size, 5 * self.tile_size),     # 右上
            City("Town C", 5 * self.tile_size, 25 * self.tile_size),     # 左下
            City("Town D", 23 * self.tile_size, 23 * self.tile_size),    # 右下
        ]
        
        # プレイヤーリスト（それぞれ異なるCityに配置）
        self.players = [
            Player(self.cities[0].x, self.cities[0].y),  # プレイヤー1 → Town A
            Player(self.cities[2].x, self.cities[2].y),  # プレイヤー2 → Town C
        ]
        
        # City間の道路を定義
        self.roads = [
            Road(self.cities[0], self.cities[1]),  # Town A - Town B
            Road(self.cities[0], self.cities[2]),  # Town A - Town C
            Road(self.cities[1], self.cities[3]),  # Town B - Town D
            Road(self.cities[2], self.cities[3]),  # Town C - Town D
            Road(self.cities[0], self.cities[3]),  # Town A - Town D (対角線)
        ]
        
        # City周辺を通行可能にする
        self.clear_city_areas()
        
    def clear_city_areas(self):
        """City周辺を通行可能にする"""
        for city in self.cities:
            # Cityの中心座標をタイル座標に変換
            center_col = int(city.x // self.tile_size)
            center_row = int(city.y // self.tile_size)
            
            # City周辺3x3エリアを通行可能にする
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    row = center_row + dr
                    col = center_col + dc
                    if 0 < row < self.map_height - 1 and 0 < col < self.map_width - 1:
                        self.map_data[row][col] = 0
                        
    def generate_30x30_map(self):
        """30x30のマップを生成"""
        map_data = []
        for row in range(30):
            map_row = []
            for col in range(30):
                # 外周は壁
                if row == 0 or row == 29 or col == 0 or col == 29:
                    map_row.append(1)
                # 内部にランダムに壁を配置
                elif (row % 4 == 0 and col % 4 == 0) or (row % 6 == 2 and col % 6 == 2):
                    map_row.append(1)
                # 特定のパターンで壁を配置
                elif (row % 8 == 3 and col % 3 == 1) or (row % 5 == 1 and col % 7 == 4):
                    map_row.append(1)
                else:
                    map_row.append(0)
            map_data.append(map_row)
        return map_data
        
    def can_move_to(self, x, y):
        """指定座標に移動可能かチェック"""
        half_width = char_width // 2
        half_height = char_height // 2
        corners = [
            (x - half_width, y - half_height),  # 左上
            (x + half_width, y - half_height),  # 右上
            (x - half_width, y + half_height),  # 左下
            (x + half_width, y + half_height)   # 右下
        ]
        
        # 各角がマップ範囲内かつ壁でないかチェック
        for corner_x, corner_y in corners:
            # マップ座標に変換
            map_col = int(corner_x // self.tile_size)
            map_row = int(corner_y // self.tile_size)
            
            # マップ範囲外は移動不可
            if map_col < 0 or map_col >= self.map_width or map_row < 0 or map_row >= self.map_height:
                return False
                
            # 壁は移動不可
            if self.map_data[map_row][map_col] == 1:
                return False
                
        return True
        
    def get_player_at_position(self, screen_x, screen_y):
        """指定したスクリーン座標にいるプレイヤーを取得"""
        # スクリーン座標をワールド座標に変換
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y
        
        for player in self.players:
            # プレイヤーの範囲内かチェック
            half_width = player.width // 2
            half_height = player.height // 2
            if (player.x - half_width <= world_x <= player.x + half_width and
                player.y - half_height <= world_y <= player.y + half_height):
                return player
        return None
        
    def get_city_at_position(self, screen_x, screen_y):
        """指定したスクリーン座標にあるCityを取得"""
        # スクリーン座標をワールド座標に変換
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y
        
        for city in self.cities:
            # Cityの範囲内かチェック
            half_size = city.size // 2
            if (city.x - half_size <= world_x <= city.x + half_size and
                city.y - half_size <= world_y <= city.y + half_size):
                return city
        return None
        
    def line_intersects_screen(self, x1, y1, x2, y2):
        """線分が画面と交差するかチェック"""
        # 画面の境界
        screen_left = 0
        screen_right = screen_width
        screen_top = 0
        screen_bottom = screen_height
        
        # 両端点が画面内にある場合
        if (screen_left <= x1 <= screen_right and screen_top <= y1 <= screen_bottom) or \
           (screen_left <= x2 <= screen_right and screen_top <= y2 <= screen_bottom):
            return True
        
        # 線分のバウンディングボックスが画面と交差するかチェック
        line_left = min(x1, x2)
        line_right = max(x1, x2)
        line_top = min(y1, y2)
        line_bottom = max(y1, y2)
        
        # バウンディングボックスが画面と重複しない場合は交差しない
        if line_right < screen_left or line_left > screen_right or \
           line_bottom < screen_top or line_top > screen_bottom:
            return False
        
        # より詳細な線分交差判定（線分が画面境界と交差するかチェック）
        return (self.line_intersects_line(x1, y1, x2, y2, screen_left, screen_top, screen_right, screen_top) or   # 上辺
                self.line_intersects_line(x1, y1, x2, y2, screen_right, screen_top, screen_right, screen_bottom) or # 右辺
                self.line_intersects_line(x1, y1, x2, y2, screen_right, screen_bottom, screen_left, screen_bottom) or # 下辺
                self.line_intersects_line(x1, y1, x2, y2, screen_left, screen_bottom, screen_left, screen_top))      # 左辺
    
    def line_intersects_line(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """2つの線分が交差するかチェック"""
        def ccw(ax, ay, bx, by, cx, cy):
            return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)
        
        return ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and \
               ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4)
        
    def update(self):
        # Qキーでタイトルシーンに戻る
        if pyxel.btnp(pyxel.KEY_Q):
            from game import TitleScene
            return TitleScene()
        # マウスクリック検出
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.click_x = pyxel.mouse_x
            self.click_y = pyxel.mouse_y
            self.click_timer = 120  # 4秒間表示（30fps * 4秒）
            
            # クリック位置にプレイヤーがいるかチェック
            clicked_player = self.get_player_at_position(self.click_x, self.click_y)
            clicked_city = self.get_city_at_position(self.click_x, self.click_y)
            
            if clicked_player:
                # プレイヤーを選択
                self.selected_player = clicked_player
            elif clicked_city and self.selected_player:
                # 選択中のプレイヤーをCityに移動
                self.selected_player.target_x = clicked_city.x
                self.selected_player.target_y = clicked_city.y
                self.selected_player.is_moving = True
            elif self.selected_player:
                # 選択中のプレイヤーを移動目標に設定
                world_x = self.click_x + self.camera_x
                world_y = self.click_y + self.camera_y
                self.selected_player.target_x = world_x
                self.selected_player.target_y = world_y
                self.selected_player.is_moving = True
        
        # クリック座標表示時間を減らす
        if self.click_timer > 0:
            self.click_timer -= 1

        # プレイヤーの移動処理
        for player in self.players:
            if player.is_moving and player.target_x is not None and player.target_y is not None:
                # 目標地点への移動ベクトルを計算
                dx = player.target_x - player.x
                dy = player.target_y - player.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                # 移動方向に基づいて向きを更新
                if abs(dx) > 1:  # 横方向の移動が十分大きい場合のみ向きを変更
                    player.facing_right = dx > 0
                
                if distance <= player.speed:
                    # 目標地点に到達
                    player.x = player.target_x
                    player.y = player.target_y
                    player.is_moving = False
                    player.target_x = None
                    player.target_y = None
                else:
                    # 目標地点に向かって移動
                    player.x += (dx / distance) * player.speed
                    player.y += (dy / distance) * player.speed
            
        # カメラの移動（WASDキー）
        if pyxel.btn(pyxel.KEY_W):
            self.camera_y -= self.camera_speed
        if pyxel.btn(pyxel.KEY_S):
            self.camera_y += self.camera_speed
        if pyxel.btn(pyxel.KEY_A):
            self.camera_x -= self.camera_speed
        if pyxel.btn(pyxel.KEY_D):
            self.camera_x += self.camera_speed
            
        # カメラ位置をマップ範囲内に制限
        self.camera_x = max(0, min(self.camera_x, self.map_pixel_width - screen_width))
        self.camera_y = max(0, min(self.camera_y, self.map_pixel_height - screen_height))
        
        return self


    def draw(self):
        pyxel.cls(3)  # 背景色
        
        # 画面に表示するタイルの範囲を計算
        start_col = int(self.camera_x // self.tile_size)
        end_col = min(int((self.camera_x + screen_width) // self.tile_size) + 1, self.map_width)
        start_row = int(self.camera_y // self.tile_size)
        end_row = min(int((self.camera_y + screen_height) // self.tile_size) + 1, self.map_height)
        
        # マップを描画（カメラ位置を考慮）
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if 0 <= row < self.map_height and 0 <= col < self.map_width:
                    x = col * self.tile_size - self.camera_x
                    y = row * self.tile_size - self.camera_y
                    
                    if self.map_data[row][col] == 1:
                        # 壁（茶色）
                        pyxel.rect(x, y, self.tile_size, self.tile_size, 4)
                    else:
                        # 床（薄い色）
                        pyxel.rect(x, y, self.tile_size, self.tile_size, 6)
        
        # 道路を描画（Cityよりも先に描画して背景に）
        for road in self.roads:
            city1_screen_x = road.city1.x - self.camera_x
            city1_screen_y = road.city1.y - self.camera_y
            city2_screen_x = road.city2.x - self.camera_x
            city2_screen_y = road.city2.y - self.camera_y
            
            # 線分が画面と交差するかチェック（より正確な判定）
            if self.line_intersects_screen(city1_screen_x, city1_screen_y, city2_screen_x, city2_screen_y):
                pyxel.line(city1_screen_x, city1_screen_y, city2_screen_x, city2_screen_y, 9)  # オレンジ色の線
        
        # Cityを描画
        for city in self.cities:
            city_screen_x = city.x - self.camera_x
            city_screen_y = city.y - self.camera_y
            
            # Cityが画面内にある場合のみ描画
            if (-city.size <= city_screen_x <= screen_width + city.size and
                -city.size <= city_screen_y <= screen_height + city.size):
                
                half_size = city.size // 2
                # City本体（青色の円）
                pyxel.circb(city_screen_x, city_screen_y, half_size, 12)  # 青色の枠
                pyxel.circ(city_screen_x, city_screen_y, half_size - 2, 1)  # 濃い青の内部
                
                # City名前を表示
                text_x = city_screen_x - len(city.name) * 2
                text_y = city_screen_y + half_size + 2
                pyxel.text(text_x, text_y, city.name, 7)  # 白文字

        # プレイヤーを描画（カメラ位置を考慮）
        for i, player in enumerate(self.players):
            player_screen_x = player.x - self.camera_x
            player_screen_y = player.y - self.camera_y
            
            # プレイヤーが画面内にある場合のみ描画
            if (-player.width <= player_screen_x <= screen_width + player.width and
                -player.height <= player_screen_y <= screen_height + player.height):
                
                # プレイヤーキャラクター（resources.pyxresのImage0左上16x16ビットマップ）
                half_width = player.width // 2
                half_height = player.height // 2
                
                # アニメーションフレームを計算（2つのフレームを交互に表示）
                anim_frame = (pyxel.frame_count // 10) % 2
                src_x = anim_frame * 16  # 0または16
                
                # 向いている方向に応じて描画幅を調整（右向きの場合は負の値で反転）
                draw_width = player.width if not player.facing_right else -player.width
                
                pyxel.blt(
                    int(player_screen_x - half_width), 
                    int(player_screen_y - half_height), 
                    0,  # Image Bank 0
                    src_x,  # ソース画像のX座標（0または16）
                    0,  # ソース画像のY座標（左上）
                    draw_width, # 幅（負の値で左右反転）
                    player.height, # 高さ
                    0   # 透明色（黒を透明にする）
                )
                
                # 選択されたプレイヤーに点滅する枠線を描画
                if player == self.selected_player:
                    # 点滅効果（30フレームで1回点滅）
                    if (pyxel.frame_count // 10) % 3 != 0:                        # 枠線の色（明るい色で目立つように）
                        frame_color = 11  # ライトブルー
                        
                        # 枠線を描画
                        frame_x = int(player_screen_x - half_width - 1)
                        frame_y = int(player_screen_y - half_height - 1)
                        frame_w = player.width + 2
                        frame_h = player.height + 2
                        
                        # 上下の線
                        pyxel.rect(frame_x, frame_y, frame_w, 1, frame_color)
                        pyxel.rect(frame_x, frame_y + frame_h - 1, frame_w, 1, frame_color)
                        # 左右の線
                        pyxel.rect(frame_x, frame_y, 1, frame_h, frame_color)
                        pyxel.rect(frame_x + frame_w - 1, frame_y, 1, frame_h, frame_color)

        # UI表示
        pyxel.text(5, 5, "Map Scene (30x30) - Press Q to Title", 7)
        pyxel.text(5, 15, "WASD: Move Camera", 7)
        pyxel.text(5, 25, "Click: Select player, Click City: Move to City", 7)
        
        # 選択中のプレイヤー情報を表示
        if self.selected_player:
            selected_text = f"Selected Player: ({int(self.selected_player.x)}, {int(self.selected_player.y)})"
            pyxel.text(5, 35, selected_text, 11)
        else:
            pyxel.text(5, 35, "No player selected", 8)
        
        # カメラ位置を表示
        camera_text = f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})"
        pyxel.text(5, 45, camera_text, 10)
        
        # Cities情報を表示
        pyxel.text(5, 65, "Cities:", 14)
        for i, city in enumerate(self.cities):
            city_info = f"{city.name}: ({int(city.x)}, {int(city.y)})"
            pyxel.text(5, 75 + i * 8, city_info, 12)
        
        # マウスクリック座標を表示
        if self.click_timer > 0:
            coord_text = f"Click: ({self.click_x}, {self.click_y})"
            pyxel.text(5, 115, coord_text, 8)
            
        # 現在のマウス座標も表示
        mouse_text = f"Mouse: ({pyxel.mouse_x}, {pyxel.mouse_y})"
        pyxel.text(5, 125, mouse_text, 10)
