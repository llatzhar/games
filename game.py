import pyxel

fps = 30  # FPSを30で定義
pyxres_file = "resources.pyxres"  # pyxresファイル名を変数で定義
screen_width = 320  # スクリーン幅
screen_height = 240  # スクリーン高さ
char_width = 16  # キャラクター幅
char_height = 16  # キャラクター高さ

class Scene:
    def __init__(self):
        self.sub_scene = None  # サブシーン
    
    def update(self):
        # サブシーンがある場合はサブシーンを優先
        if self.sub_scene:
            result = self.sub_scene.update()
            if result is None:  # サブシーンが終了
                # サブシーン終了時のコールバック処理
                self.on_sub_scene_finished(self.sub_scene)
                self.sub_scene = None
                return False  # サブシーン終了、メイン処理を続行
            return True  # サブシーン実行中
        
        # サブシーンがない場合はメイン処理を実行
        return False
    
    def on_sub_scene_finished(self, finished_sub_scene):
        """サブシーン終了時に呼び出されるコールバック（継承クラスでオーバーライド可能）"""
        pass

    def draw(self):
        # サブシーンがある場合はサブシーンを描画
        if self.sub_scene:
            self.sub_scene.draw()
            return True  # サブシーンを描画した
        
        # サブシーンがない場合はメイン描画を実行
        return False
    
    def set_sub_scene(self, sub_scene):
        """サブシーンを設定"""
        self.sub_scene = sub_scene

class SubScene(Scene):
    """サブシーンの基底クラス"""
    def __init__(self, parent_scene):
        super().__init__()
        self.parent_scene = parent_scene
    
    def finish(self):
        """サブシーンを終了（Noneを返すことで親シーンに制御を戻す）"""
        return None

class TitleScene(Scene):
    def update(self):
        # サブシーンの処理を先に実行
        if super().update():
            return self
        
        # メインの処理
        if pyxel.btnp(pyxel.KEY_SPACE):
            return GameScene()
        if pyxel.btnp(pyxel.KEY_RETURN):
            from map import MapScene
            return MapScene()
        return self

    def draw(self):
        # サブシーンがある場合はサブシーンを描画
        if super().draw():
            return
        
        # メインの描画
        pyxel.cls(0)
        pyxel.text(40, 60, "Press SPACE to Start", pyxel.frame_count % 16)
        pyxel.text(35, 80, "Press ENTER for Map", 7)

class GameScene(Scene):
    def __init__(self):
        super().__init__()
        self.x = screen_width // 2
        self.y = screen_height // 2
        self.dir = 1  # 1:左向き, -1:右向き

    def update(self):
        # サブシーンの処理を先に実行
        if super().update():
            return self
        
        # メインの処理
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
        # サブシーンがある場合はサブシーンを描画
        if super().draw():
            return
        
        # メインの描画
        pyxel.cls(1)
        anim_frame = (pyxel.frame_count // 10) % 2
        sx = 0 if anim_frame == 0 else char_width
        # dir=1:そのまま, dir=-1:左右反転
        pyxel.blt(self.x, self.y, 0, sx, 0, char_width * self.dir, char_height, 2)
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
