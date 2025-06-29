import pyxel

# game.pyから定数をインポート
from game import screen_width, screen_height, char_width, char_height, Scene

class MapScene(Scene):
    def __init__(self):
        self.click_x = -1  # クリック位置のX座標
        self.click_y = -1  # クリック位置のY座標
        self.click_timer = 0  # クリック座標表示時間
        
        # プレイヤーの位置（ワールド座標）
        self.player_x = 1.5 * 16  # マップ座標1.5タイル目
        self.player_y = 1.5 * 16  # マップ座標1.5タイル目
        self.player_size = 16  # プレイヤーのサイズ（16x16ビットマップに合わせて）
        self.player_speed = 2  # プレイヤーの移動速度
        
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
        # プレイヤーの四隅の座標を計算
        half_size = self.player_size // 2
        corners = [
            (x - half_size, y - half_size),  # 左上
            (x + half_size, y - half_size),  # 右上
            (x - half_size, y + half_size),  # 左下
            (x + half_size, y + half_size)   # 右下
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
            
        # クリック座標表示時間を減らす
        if self.click_timer > 0:
            self.click_timer -= 1
            
        # プレイヤーの移動（WASDキー）
        old_player_x, old_player_y = self.player_x, self.player_y
        
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
        
        # プレイヤーを描画（カメラ位置を考慮）
        player_screen_x = self.player_x - self.camera_x
        player_screen_y = self.player_y - self.camera_y
        
        # プレイヤーが画面内にある場合のみ描画
        if (-self.player_size <= player_screen_x <= screen_width + self.player_size and
            -self.player_size <= player_screen_y <= screen_height + self.player_size):
            # プレイヤーキャラクター（resources.pyxresのImage0左上16x16ビットマップ）
            half_size = self.player_size // 2
            pyxel.blt(
                int(player_screen_x - half_size), 
                int(player_screen_y - half_size), 
                0,  # Image Bank 0
                0,  # ソース画像のX座標（左上）
                0,  # ソース画像のY座標（左上）
                16, # 幅
                16, # 高さ
                0   # 透明色（黒を透明にする）
            )
        
        # UI表示
        pyxel.text(5, 5, "Map Scene (30x30) - Press Q to Title", 7)
        pyxel.text(5, 15, "WASD: Move Camera", 7)
        
        # プレイヤー位置を表示（マップ上の実際の座標）
        player_text = f"Player: ({int(self.player_x)}, {int(self.player_y)})"
        pyxel.text(5, 25, player_text, 11)
        
        # カメラ位置を表示
        camera_text = f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})"
        pyxel.text(5, 35, camera_text, 10)
        
        # マウスクリック座標を表示
        if self.click_timer > 0:
            coord_text = f"Click: ({self.click_x}, {self.click_y})"
            pyxel.text(5, 45, coord_text, 8)
            
        # 現在のマウス座標も表示
        mouse_text = f"Mouse: ({pyxel.mouse_x}, {pyxel.mouse_y})"
        pyxel.text(5, 110, mouse_text, 10)
