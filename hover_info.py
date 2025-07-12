import pyxel
from game import screen_width, screen_height

class HoverInfo:
    """マウスカーソルが重なった際の情報表示クラス"""
    
    def __init__(self):
        self.padding = 4  # 枠の内側の余白
        self.line_height = 8  # 行の高さ
        self.min_width = 60  # 最小幅
        self.border_color = 7  # 枠の色（白）
        self.bg_color = 0     # 背景色（黒）
        self.text_color = 7   # テキスト色（白）
        
    def get_text_width(self, text):
        """テキストの幅を計算"""
        return len(text) * 4  # pyxelのフォント幅は4ピクセル
    
    def calculate_info_box_size(self, info_lines):
        """情報ボックスのサイズを計算"""
        if not info_lines:
            return 0, 0
            
        # 最大テキスト幅を求める
        max_text_width = max(self.get_text_width(line) for line in info_lines)
        box_width = max(self.min_width, max_text_width + self.padding * 2)
        box_height = len(info_lines) * self.line_height + self.padding * 2
        
        return box_width, box_height
    
    def calculate_position(self, mouse_x, mouse_y, box_width, box_height):
        """情報ボックスの表示位置を計算（マウスカーソルと逆サイドに配置）"""
        offset = 10  # マウスカーソルからの距離
        
        # 画面の中央より右にマウスがある場合は左側に表示、左にある場合は右側に表示
        if mouse_x > screen_width // 2:
            # 左側に表示
            info_x = mouse_x - box_width - offset
            if info_x < 0:
                info_x = 0
        else:
            # 右側に表示
            info_x = mouse_x + offset
            if info_x + box_width > screen_width:
                info_x = screen_width - box_width
        
        # 画面の中央より下にマウスがある場合は上側に表示、上にある場合は下側に表示
        if mouse_y > screen_height // 2:
            # 上側に表示
            info_y = mouse_y - box_height - offset
            if info_y < 0:
                info_y = 0
        else:
            # 下側に表示
            info_y = mouse_y + offset
            if info_y + box_height > screen_height:
                info_y = screen_height - box_height
        
        return info_x, info_y
    
    def draw_info_box(self, mouse_x, mouse_y, info_lines):
        """情報ボックスを描画"""
        if not info_lines:
            return
            
        box_width, box_height = self.calculate_info_box_size(info_lines)
        info_x, info_y = self.calculate_position(mouse_x, mouse_y, box_width, box_height)
        
        # 背景を描画
        pyxel.rect(info_x, info_y, box_width, box_height, self.bg_color)
        
        # 枠を描画
        pyxel.rectb(info_x, info_y, box_width, box_height, self.border_color)
        
        # テキストを描画
        text_x = info_x + self.padding
        text_y = info_y + self.padding
        
        for line in info_lines:
            pyxel.text(text_x, text_y, line, self.text_color)
            text_y += self.line_height
    
    def get_character_info(self, character):
        """キャラクターの情報を取得"""
        info_lines = []
        
        # キャラクタータイプを判定
        char_type = "Player" if hasattr(character, 'image_index') and not hasattr(character, 'ai_type') else "Enemy"
        
        if char_type == "Enemy":
            # 敵の場合
            info_lines.append(f"Enemy ({character.ai_type})")
            current_city = character.current_city_name if character.current_city_name else "None"
            info_lines.append(f"Location: {current_city}")
            info_lines.append(f"Life: {character.life}/{character.max_life}")
            info_lines.append(f"Attack: {character.attack}")
            
            # AI特性の説明
            if character.ai_type == "aggressive":
                info_lines.append("Pursues players")
            elif character.ai_type == "defensive":
                info_lines.append("Avoids players")
            elif character.ai_type == "patrol":
                info_lines.append("Patrols route")
            elif character.ai_type == "random":
                info_lines.append("Moves randomly")
        else:
            # プレイヤーの場合
            info_lines.append("Player")
            current_city = character.current_city_name if character.current_city_name else "None"
            info_lines.append(f"Location: {current_city}")
            info_lines.append(f"Life: {character.life}/{character.max_life}")
            info_lines.append(f"Attack: {character.attack}")
            
            if character.is_moving:
                info_lines.append("Moving...")
        
        return info_lines
    
    def get_city_info(self, city):
        """都市の情報を取得"""
        info_lines = []
        
        info_lines.append(f"City: {city.name}")
        info_lines.append(f"Position: ({int(city.x)}, {int(city.y)})")
        info_lines.append(f"Size: {city.size}")
        
        return info_lines
    
    def draw_hover_info(self, mouse_x, mouse_y, hovered_character, hovered_city):
        """ホバー情報を描画（キャラクターを優先）"""
        info_lines = []
        
        if hovered_character:
            # キャラクターが優先
            info_lines = self.get_character_info(hovered_character)
        elif hovered_city:
            # キャラクターがない場合は都市の情報
            info_lines = self.get_city_info(hovered_city)
        
        if info_lines:
            self.draw_info_box(mouse_x, mouse_y, info_lines)
