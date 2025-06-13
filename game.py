import pyxel

class Scene:
    def update(self):
        pass

    def draw(self):
        pass

class TitleScene(Scene):
    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            return GameScene()
        return self

    def draw(self):
        pyxel.cls(0)
        pyxel.text(40, 60, "Press SPACE to Start", pyxel.frame_count % 16)

class GameScene(Scene):
    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            return TitleScene()
        return self

    def draw(self):
        pyxel.cls(1)
        # Image0の左上16x16のキャラクタを画面中央(80,60)に表示
        pyxel.blt(80, 60, 0, 0, 0, 16, 16, 0)
        pyxel.text(40, 80, "Game Scene - Press Q to Quit", 7)

class App:
    def __init__(self):
        # 'caption' argument is not supported in some Pyxel versions
        pyxel.init(160, 120)
        pyxel.load("resources.pyxres")
        self.scene = TitleScene()
        pyxel.run(self.update, self.draw)

    def update(self):
        next_scene = self.scene.update()
        if next_scene is not self.scene:
            self.scene = next_scene

    def draw(self):
        self.scene.draw()

if __name__ == "__main__":
    App()
