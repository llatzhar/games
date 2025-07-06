import pyxel
from game import SubScene

class BattleSubScene(SubScene):
    def __init__(self, parent_scene, battle_result, city):
        super().__init__(parent_scene)
        self.battle_result = battle_result
        self.city = city
        self.animation_timer = 0
        self.max_animation_time = 240  # 8秒間（30fps * 8秒）
        self.phase = "intro"  # intro -> player_attack -> enemy_attack -> results -> outro
        self.phase_timer = 0
        self.damage_numbers = []  # ダメージ表示用
        
        # 戦闘ログから情報を抽出
        self.parse_battle_log()
        
    def parse_battle_log(self):
        """戦闘ログから表示用の情報を抽出"""
        self.player_damage = 0
        self.enemy_damage = 0
        self.target_enemy_type = "enemy"
        
        for log_entry in self.battle_result['log']:
            if "Players dealt" in log_entry:
                # "Players dealt 25 damage to aggressive enemy in Town A"
                parts = log_entry.split()
                if len(parts) >= 3:
                    self.player_damage = int(parts[2])
                if "aggressive" in log_entry:
                    self.target_enemy_type = "aggressive"
                elif "patrol" in log_entry:
                    self.target_enemy_type = "patrol"
                elif "defensive" in log_entry:
                    self.target_enemy_type = "defensive"
                elif "random" in log_entry:
                    self.target_enemy_type = "random"
                    
            elif "Enemies dealt" in log_entry:
                # "Enemies dealt 20 damage to player in Town A"
                parts = log_entry.split()
                if len(parts) >= 3:
                    self.enemy_damage = int(parts[2])
    
    def update(self):
        self.animation_timer += 1
        self.phase_timer += 1
        
        # フェーズ管理
        if self.phase == "intro" and self.phase_timer >= 60:  # 2秒
            self.phase = "player_attack"
            self.phase_timer = 0
            if self.player_damage > 0:
                self.add_damage_number(self.player_damage, "player")
                
        elif self.phase == "player_attack" and self.phase_timer >= 60:  # 2秒
            self.phase = "enemy_attack"
            self.phase_timer = 0
            if self.enemy_damage > 0:
                self.add_damage_number(self.enemy_damage, "enemy")
                
        elif self.phase == "enemy_attack" and self.phase_timer >= 60:  # 2秒
            self.phase = "results"
            self.phase_timer = 0
            
        elif self.phase == "results" and self.phase_timer >= 90:  # 3秒
            self.phase = "outro"
            self.phase_timer = 0
            
        elif self.phase == "outro" and self.phase_timer >= 30:  # 1秒
            return None  # サブシーン終了
        
        # ダメージナンバーの更新
        self.damage_numbers = [(damage, attacker, timer-1) for damage, attacker, timer in self.damage_numbers if timer > 0]
        
        # ESCキーまたはスペースキーで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            return None
            
        return self
    
    def add_damage_number(self, damage, attacker):
        """ダメージ数値を追加"""
        self.damage_numbers.append((damage, attacker, 90))  # 3秒間表示
    
    def draw(self):
        # 半透明の黒い背景
        pyxel.rect(0, 0, pyxel.width, pyxel.height, 0)
        
        # メイン情報表示エリア
        info_x = pyxel.width // 2
        info_y = pyxel.height // 2
        
        # 都市名表示
        city_text = f"BATTLE AT {self.city.name}"
        text_width = len(city_text) * 4
        pyxel.text(info_x - text_width // 2, info_y - 60, city_text, 7)
        
        # フェーズ別の表示
        if self.phase == "intro":
            intro_text = "Battle begins!"
            text_width = len(intro_text) * 4
            pyxel.text(info_x - text_width // 2, info_y - 20, intro_text, 11)
            
        elif self.phase == "player_attack":
            if self.player_damage > 0:
                attack_text = f"Players attack for {self.player_damage} damage!"
                text_width = len(attack_text) * 4
                pyxel.text(info_x - text_width // 2, info_y - 20, attack_text, 11)
                
                # プレイヤー攻撃エフェクト（青色の閃光）
                if self.phase_timer < 30:
                    flash_intensity = max(0, 30 - self.phase_timer)
                    if flash_intensity > 15:
                        pyxel.rect(0, 0, pyxel.width, pyxel.height, 12)
            else:
                miss_text = "Player attack missed!"
                text_width = len(miss_text) * 4
                pyxel.text(info_x - text_width // 2, info_y - 20, miss_text, 8)
                
        elif self.phase == "enemy_attack":
            if self.enemy_damage > 0:
                attack_text = f"Enemies attack for {self.enemy_damage} damage!"
                text_width = len(attack_text) * 4
                pyxel.text(info_x - text_width // 2, info_y - 20, attack_text, 8)
                
                # 敵攻撃エフェクト（赤色の閃光）
                if self.phase_timer < 30:
                    flash_intensity = max(0, 30 - self.phase_timer)
                    if flash_intensity > 15:
                        pyxel.rect(0, 0, pyxel.width, pyxel.height, 8)
            else:
                miss_text = "Enemy attack missed!"
                text_width = len(miss_text) * 4
                pyxel.text(info_x - text_width // 2, info_y - 20, miss_text, 11)
                
        elif self.phase == "results":
            result_text = "Battle concluded"
            text_width = len(result_text) * 4
            pyxel.text(info_x - text_width // 2, info_y - 20, result_text, 10)
            
            # 戦闘前後の兵力表示
            battle_summary = f"Players: {self.battle_result['players_before']}, Enemies: {self.battle_result['enemies_before']}"
            summary_width = len(battle_summary) * 4
            pyxel.text(info_x - summary_width // 2, info_y, battle_summary, 6)
            
        elif self.phase == "outro":
            # フェードアウト効果
            fade_alpha = min(self.phase_timer * 8, 255)
            if fade_alpha < 128:
                outro_text = "Press SPACE or ESC to continue"
                text_width = len(outro_text) * 4
                pyxel.text(info_x - text_width // 2, info_y + 20, outro_text, 6)
        
        # ダメージナンバーの表示
        for damage, attacker, timer in self.damage_numbers:
            if timer > 0:
                # ダメージ数値の位置（上に浮かび上がる効果）
                float_y = info_y + 10 - (90 - timer) // 3
                color = 11 if attacker == "player" else 8
                
                damage_text = f"-{damage}"
                text_width = len(damage_text) * 4
                pyxel.text(info_x - text_width // 2, float_y, damage_text, color)
        
        # プログレスバー
        progress = min(1.0, self.animation_timer / self.max_animation_time)
        bar_width = pyxel.width - 40
        bar_x = 20
        bar_y = pyxel.height - 20
        
        # プログレスバーの背景
        pyxel.rect(bar_x, bar_y, bar_width, 4, 5)
        # プログレスバーの進行状況
        pyxel.rect(bar_x, bar_y, int(bar_width * progress), 4, 10)
        
        # スキップ指示
        skip_text = "SPACE/ESC: Skip"
        pyxel.text(pyxel.width - len(skip_text) * 4 - 5, 5, skip_text, 6)
