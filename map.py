import pyxel

# game.pyから定数をインポート
from game import screen_width, screen_height, char_width, char_height, Scene

class MapScene(Scene):
    def __init__(self):
        self.player_x = screen_width // 2
        self.player_y = screen_height // 2
        self.dir = 1  # 1:左向き, -1:右向き
        
        # マップデータ（簡単な例）
        self.map_data = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 0, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
        
        self.tile_size = 16
        
    def update(self):
        # Qキーでタイトルシーンに戻る
        if pyxel.btnp(pyxel.KEY_Q):
            from game import TitleScene
            return TitleScene()
            
        # プレイヤーの移動
        old_x, old_y = self.player_x, self.player_y
        
        if pyxel.btn(pyxel.KEY_W):
            self.player_y -= 2
        if pyxel.btn(pyxel.KEY_S):
            self.player_y += 2
        if pyxel.btn(pyxel.KEY_A):
            self.player_x -= 2
            self.dir = 1  # 左向き
        if pyxel.btn(pyxel.KEY_D):
            self.player_x += 2
            self.dir = -1  # 右向き
            
        # 壁との衝突判定
        if self.check_collision(self.player_x, self.player_y):
            self.player_x, self.player_y = old_x, old_y
            
        # 画面外に出ないよう制限
        self.player_x = max(0, min(self.player_x, screen_width - char_width))
        self.player_y = max(0, min(self.player_y, screen_height - char_height))
        
        return self
        
    def check_collision(self, x, y):
        """プレイヤーとマップの衝突判定"""
        # プレイヤーの四隅をチェック
        corners = [
            (x, y),
            (x + char_width - 1, y),
            (x, y + char_height - 1),
            (x + char_width - 1, y + char_height - 1)
        ]
        
        for corner_x, corner_y in corners:
            map_x = corner_x // self.tile_size
            map_y = corner_y // self.tile_size
            
            if (0 <= map_y < len(self.map_data) and 
                0 <= map_x < len(self.map_data[0]) and
                self.map_data[map_y][map_x] == 1):
                return True
        return False
        
    def draw(self):
        pyxel.cls(3)  # 背景色
        
        # マップを描画
        for row in range(len(self.map_data)):
            for col in range(len(self.map_data[row])):
                x = col * self.tile_size
                y = row * self.tile_size
                
                if self.map_data[row][col] == 1:
                    # 壁（茶色）
                    pyxel.rect(x, y, self.tile_size, self.tile_size, 4)
                else:
                    # 床（薄い色）
                    pyxel.rect(x, y, self.tile_size, self.tile_size, 6)
                    
        # プレイヤーを描画
        anim_frame = (pyxel.frame_count // 10) % 2
        sx = 0 if anim_frame == 0 else char_width
        pyxel.blt(self.player_x, self.player_y, 0, sx, 0, char_width * self.dir, char_height, 0)
        
        # UI表示
        pyxel.text(5, 5, "Map Scene - Press Q to Title", 7)
