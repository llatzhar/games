import pyxel

# game.pyから定数をインポート
from game import screen_width, screen_height, char_width, char_height, Scene

class MapScene(Scene):
    def __init__(self):
        self.click_x = -1  # クリック位置のX座標
        self.click_y = -1  # クリック位置のY座標
        self.click_timer = 0  # クリック座標表示時間
        
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
            
        # カメラの移動（WASDキー）
        old_camera_x, old_camera_y = self.camera_x, self.camera_y
        
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
        start_col = self.camera_x // self.tile_size
        end_col = min((self.camera_x + screen_width) // self.tile_size + 1, self.map_width)
        start_row = self.camera_y // self.tile_size
        end_row = min((self.camera_y + screen_height) // self.tile_size + 1, self.map_height)
        
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
        
        # UI表示
        pyxel.text(5, 5, "Map Scene (30x30) - Press Q to Title", 7)
        pyxel.text(5, 15, "WASD: Move Camera View", 7)
        
        # カメラ位置を表示
        camera_text = f"Camera: ({self.camera_x}, {self.camera_y})"
        pyxel.text(5, 25, camera_text, 10)
        
        # マウスクリック座標を表示
        if self.click_timer > 0:
            coord_text = f"Click: ({self.click_x}, {self.click_y})"
            pyxel.text(5, 35, coord_text, 8)
            
        # 現在のマウス座標も表示
        mouse_text = f"Mouse: ({pyxel.mouse_x}, {pyxel.mouse_y})"
        pyxel.text(5, 110, mouse_text, 10)
