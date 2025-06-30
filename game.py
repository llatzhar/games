import pyxel

fps = 30  # FPSを30で定義
pyxres_file = "resources.pyxres"  # pyxresファイル名を変数で定義
screen_width = 160  # スクリーン幅
screen_height = 120  # スクリーン高さ
char_width = 16  # キャラクター幅
char_height = 16  # キャラクター高さ

class Scene:
    def update(self):
        pass

    def draw(self):
        pass

class TitleScene(Scene):
    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            return GameScene()
        if pyxel.btnp(pyxel.KEY_RETURN):
            from map import MapScene
            return MapScene()
        return self

    def draw(self):
        pyxel.cls(0)
        pyxel.text(40, 60, "Press SPACE to Start", pyxel.frame_count % 16)
        pyxel.text(35, 80, "Press ENTER for Map", 7)

class GameScene(Scene):
    def __init__(self):
        self.x = screen_width // 2
        self.y = screen_height // 2
        self.dir = 1  # 1:左向き, -1:右向き

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            return TitleScene()
        moved = False
        # WASDで移動
        if pyxel.btn(pyxel.KEY_W):
            self.y -= 2
            moved = True
        if pyxel.btn(pyxel.KEY_S):
            self.y += 2
            moved = True
        if pyxel.btn(pyxel.KEY_A):
            self.x -= 2
            self.dir = 1  # 左向き
            moved = True
        if pyxel.btn(pyxel.KEY_D):
            self.x += 2
            self.dir = -1  # 右向き
            moved = True
        # 画面外に出ないよう制限
        self.x = max(0, min(self.x, screen_width - char_width))
        self.y = max(0, min(self.y, screen_height - char_height))
        return self

    def draw(self):
        pyxel.cls(1)
        anim_frame = (pyxel.frame_count // 10) % 2
        sx = 0 if anim_frame == 0 else char_width
        # dir=1:そのまま, dir=-1:左右反転
        pyxel.blt(self.x, self.y, 0, sx, 0, char_width * self.dir, char_height, 0)
        pyxel.text(40, 80, "Game Scene - Press Q to Quit", 7)

class App:
    def __init__(self):
        # 'caption' argument is not supported in some Pyxel versions
        # quit_key=pyxel.KEY_NONE でESCキーでの終了を無効化
        pyxel.init(screen_width, screen_height, fps=fps, quit_key=pyxel.KEY_NONE)  # 変数を適用
        pyxel.load(pyxres_file)
        self.scene = TitleScene()
        pyxel.run(self.update, self.draw)

    def update(self):
        next_scene = self.scene.update()
        if next_scene is not self.scene:
            # シーンの初期化処理
            if hasattr(next_scene, '__init__'):
                next_scene.__init__()
            self.scene = next_scene

    def draw(self):
        self.scene.draw()

if __name__ == "__main__":
    App()
