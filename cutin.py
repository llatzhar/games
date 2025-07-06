import pyxel
from game import screen_width, screen_height, SubScene

class CutinSubScene(SubScene):
    """カットイン演出を表示するサブシーン"""
    def __init__(self, parent_scene, text, duration=60):
        super().__init__(parent_scene)
        self.text = text
        self.duration = duration  # 演出時間（フレーム数）
        self.timer = 0
    
    def update(self):
        # 親クラスのサブシーン処理を実行（ただし、サブシーンのサブシーンは想定していない）
        if super().update():
            return self
        
        # メイン処理
        self.timer += 1
        if self.timer >= self.duration:
            return self.finish()  # サブシーンを終了
        return self
    
    def draw(self):
        # 親クラスのサブシーン描画を実行（ただし、サブシーンのサブシーンは想定していない）
        if super().draw():
            return
        
        # メイン描画
        """カットイン演出を描画"""
        # 背景を暗くする
        pyxel.rect(0, 0, screen_width, screen_height, 0)
        
        # アニメーション進行度を計算（0.0から1.0）
        progress = self.timer / self.duration
        
        # テキストの移動位置を計算（右から左へ）
        text_width = len(self.text) * 4  # 1文字4ピクセルと仮定
        start_x = screen_width + text_width  # 画面右端外から開始
        end_x = (screen_width - text_width) // 2  # 画面中央で停止
        
        # イージング（加速度的な動き）
        if progress < 0.8:
            # 最初の80%で右から中央へ移動
            eased_progress = 1 - (1 - progress / 0.8) ** 3  # イージングアウト
            text_x = start_x - (start_x - end_x) * eased_progress
        else:
            # 残り20%で中央に留まる
            text_x = end_x
        
        text_y = screen_height // 2 - 4  # 画面中央の縦位置
        
        # ターンによって色を変更
        if "PLAYER" in self.text:
            text_color = 11  # ライトブルー
            bg_color = 1     # 濃い青
        else:
            text_color = 8   # 赤
            bg_color = 2     # 濃い赤
        
        # 背景バーを描画
        bar_height = 24
        bar_y = text_y - 8
        pyxel.rect(0, bar_y, screen_width, bar_height, bg_color)
        
        # テキストを描画
        pyxel.text(int(text_x), text_y, self.text, text_color)
