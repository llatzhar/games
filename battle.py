import pyxel
from game import SubScene

class BattleSubScene(SubScene):
    def __init__(self, parent_scene, battle_info, city):
        super().__init__(parent_scene)
        self.battle_info = battle_info  # 戦闘場所情報（まだ戦闘は実行されていない）
        self.city = city
        self.animation_timer = 0
        self.max_animation_time = 240  # 8秒間（30fps * 8秒）
        self.phase = "intro"  # intro -> player_attack -> enemy_attack -> results -> outro
        self.phase_timer = 0
        self.damage_numbers = []  # ダメージ表示用
        
        # 戦闘に参加するキャラクター（戦闘開始時の状態をキャプチャ）
        self.battle_players = battle_info['players']
        self.battle_enemies = battle_info['enemies']
        
        # 戦闘開始時のライフを記録（戦闘前の状態を保存）
        self.initial_player_lives = [p.life for p in self.battle_players]
        self.initial_enemy_lives = [e.life for e in self.battle_enemies]
        
        # 戦闘計算を実行（ここで初めて実際の戦闘を行う）
        self.battle_result = self.execute_battle()
        
        # 戦闘ログから情報を抽出
        self.parse_battle_log()
        
    def execute_battle(self):
        """戦闘を実行して結果を返す"""
        battle_log = []
        city_name = self.city.name
        
        # プレイヤーの攻撃フェーズ
        total_player_attack = sum(p.attack for p in self.battle_players)
        if self.battle_enemies:
            # 最も弱い敵から攻撃
            target_enemy = min(self.battle_enemies, key=lambda e: e.life)
            damage = min(total_player_attack, target_enemy.life)
            target_enemy.life -= damage
            battle_log.append(f"Players dealt {damage} damage to {target_enemy.ai_type} enemy in {city_name}")
        
        # 敵の攻撃フェーズ
        total_enemy_attack = sum(e.attack for e in self.battle_enemies)
        if self.battle_players:
            # 最も弱いプレイヤーから攻撃
            target_player = min(self.battle_players, key=lambda p: p.life)
            damage = min(total_enemy_attack, target_player.life)
            target_player.life -= damage
            battle_log.append(f"Enemies dealt {damage} damage to player in {city_name}")
        
        return {
            'city_id': self.city.id,
            'log': battle_log,
            'players_before': len(self.battle_players),
            'enemies_before': len(self.battle_enemies)
        }
        
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
        
        # フラッシュエフェクトを最初に描画（背景の上、他の要素の下）
        self.draw_flash_effects()
        
        # キャラクター描画エリア
        self.draw_battle_characters()
        
        # メイン情報表示エリア（上部に移動）
        info_x = pyxel.width // 2
        info_y = 60  # 画面上部に移動
        
        # 都市名表示
        city_text = f"BATTLE AT {self.city.name}"
        text_width = len(city_text) * 4
        pyxel.text(info_x - text_width // 2, info_y - 30, city_text, 7)
        
        # フェーズ別の表示
        if self.phase == "intro":
            intro_text = "Battle begins!"
            text_width = len(intro_text) * 4
            pyxel.text(info_x - text_width // 2, info_y, intro_text, 11)
            
        elif self.phase == "player_attack":
            if self.player_damage > 0:
                attack_text = f"Players attack for {self.player_damage} damage!"
                text_width = len(attack_text) * 4
                pyxel.text(info_x - text_width // 2, info_y, attack_text, 11)
            else:
                miss_text = "Player attack missed!"
                text_width = len(miss_text) * 4
                pyxel.text(info_x - text_width // 2, info_y, miss_text, 8)
                
        elif self.phase == "enemy_attack":
            if self.enemy_damage > 0:
                attack_text = f"Enemies attack for {self.enemy_damage} damage!"
                text_width = len(attack_text) * 4
                pyxel.text(info_x - text_width // 2, info_y, attack_text, 8)
            else:
                miss_text = "Enemy attack missed!"
                text_width = len(miss_text) * 4
                pyxel.text(info_x - text_width // 2, info_y, miss_text, 11)
                
        elif self.phase == "results":
            result_text = "Battle concluded"
            text_width = len(result_text) * 4
            pyxel.text(info_x - text_width // 2, info_y, result_text, 10)
            
            # 戦闘前後の兵力表示
            battle_summary = f"Players: {self.battle_result['players_before']}, Enemies: {self.battle_result['enemies_before']}"
            summary_width = len(battle_summary) * 4
            pyxel.text(info_x - summary_width // 2, info_y + 20, battle_summary, 6)
            
        elif self.phase == "outro":
            # フェードアウト効果
            fade_alpha = min(self.phase_timer * 8, 255)
            if fade_alpha < 128:
                outro_text = "Press SPACE or ESC to continue"
                text_width = len(outro_text) * 4
                pyxel.text(info_x - text_width // 2, info_y + 50, outro_text, 6)
        
        # ダメージナンバーの表示
        for damage, attacker, timer in self.damage_numbers:
            if timer > 0:
                # ダメージ数値の位置を攻撃対象側に表示
                if attacker == "player":
                    # プレイヤーの攻撃 -> 敵側にダメージ表示
                    float_x = pyxel.width - 100
                else:
                    # 敵の攻撃 -> プレイヤー側にダメージ表示
                    float_x = 100
                
                # 上に浮かび上がる効果
                float_y = pyxel.height // 2 - (90 - timer) // 3
                color = 11 if attacker == "player" else 8
                
                damage_text = f"-{damage}"
                text_width = len(damage_text) * 4
                pyxel.text(float_x - text_width // 2, float_y, damage_text, color)
        
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
    
    def draw_battle_characters(self):
        """戦闘に参加するキャラクターを描画"""
        # プレイヤーキャラクターを左側に描画
        player_start_x = 50
        player_y = pyxel.height // 2 + 20
        
        for i, player in enumerate(self.battle_players):
            # プレイヤーの描画位置（縦に並べる）
            draw_x = player_start_x
            draw_y = player_y + i * 40  # 40ピクセル間隔で縦に配置
            
            # プレイヤーが画面内に収まるかチェック
            if draw_y + player.height < pyxel.height - 20:
                self.draw_character(player, draw_x, draw_y, True, self.initial_player_lives[i], "player")  # 右向き
                
                # プレイヤー名を表示
                name_text = f"Player {i+1}"
                pyxel.text(draw_x - len(name_text) * 2, draw_y - 25, name_text, 11)
                
                # ライフ表示（戦闘の進行に応じて変化）
                displayed_life = self.get_displayed_life(player, self.initial_player_lives[i], "player")
                life_text = f"HP: {displayed_life}/{player.max_life}"
                pyxel.text(draw_x - len(life_text) * 2, draw_y - 15, life_text, 7)
        
        # 敵キャラクターを右側に描画
        enemy_start_x = pyxel.width - 80
        enemy_y = pyxel.height // 2 + 20
        
        for i, enemy in enumerate(self.battle_enemies):
            # 敵の描画位置（縦に並べる）
            draw_x = enemy_start_x
            draw_y = enemy_y + i * 40  # 40ピクセル間隔で縦に配置
            
            # 敵が画面内に収まるかチェック
            if draw_y + enemy.height < pyxel.height - 20:
                self.draw_character(enemy, draw_x, draw_y, False, self.initial_enemy_lives[i], "enemy")  # 左向き
                
                # 敵名を表示
                name_text = f"Enemy {i+1}"
                pyxel.text(draw_x + 20, draw_y - 25, name_text, 8)
                
                # AI種別を表示
                ai_text = f"({enemy.ai_type})"
                pyxel.text(draw_x + 20, draw_y - 15, ai_text, 6)
                
                # ライフ表示
                # ライフ表示（戦闘の進行に応じて変化）
                displayed_life = self.get_displayed_life(enemy, self.initial_enemy_lives[i], "enemy")
                life_text = f"HP: {displayed_life}/{enemy.max_life}"
                pyxel.text(draw_x + 20, draw_y - 5, life_text, 7)
    
    def draw_character(self, character, x, y, facing_right, initial_life, character_type):
        """キャラクターを指定位置に描画"""
        half_width = character.width // 2
        half_height = character.height // 2
        
        # アニメーションフレームを計算（戦闘中はゆっくりとしたアニメーション）
        anim_frame = (pyxel.frame_count // 20) % 2
        src_x = anim_frame * 16
        src_y = character.image_index * 16
        
        # 攻撃フェーズ中は攻撃アニメーション
        if ((self.phase == "player_attack" and hasattr(character, 'attack') and character in self.battle_players) or
            (self.phase == "enemy_attack" and hasattr(character, 'ai_type') and character in self.battle_enemies)):
            # 攻撃時は少し前に出る
            if self.phase_timer < 20:
                offset_x = 5 if facing_right else -5
                x += offset_x
        
        # 向きに応じて描画幅を調整
        draw_width = character.width if facing_right else -character.width
        
        pyxel.blt(
            int(x - half_width), 
            int(y - half_height), 
            0,  # Image Bank 0
            src_x,
            src_y,
            draw_width,
            character.height,
            2   # 透明色
        )
        
        # ライフゲージを描画（戦闘進行に応じた値を使用）
        life_bar_width = character.width
        life_bar_height = 3
        life_bar_x = int(x - half_width)
        life_bar_y = int(y - half_height - 10)
        
        # ライフゲージの背景（赤色）
        pyxel.rect(life_bar_x, life_bar_y, life_bar_width, life_bar_height, 8)
        
        # 戦闘進行に応じた表示ライフ値を取得
        displayed_life = self.get_displayed_life(character, initial_life, character_type)
        
        # ライフゲージの現在値（緑色）
        current_life_width = int((displayed_life / character.max_life) * life_bar_width)
        if current_life_width > 0:
            pyxel.rect(life_bar_x, life_bar_y, current_life_width, life_bar_height, 11)
    
    def draw_flash_effects(self):
        """フラッシュエフェクトを描画（背景の上、他の要素の下）"""
        if self.phase == "player_attack" and self.player_damage > 0:
            # プレイヤー攻撃エフェクト（青色の閃光）
            if self.phase_timer < 30:
                flash_intensity = max(0, 30 - self.phase_timer)
                if flash_intensity > 15:
                    pyxel.rect(0, 0, pyxel.width, pyxel.height, 12)
                    
        elif self.phase == "enemy_attack" and self.enemy_damage > 0:
            # 敵攻撃エフェクト（赤色の閃光）
            if self.phase_timer < 30:
                flash_intensity = max(0, 30 - self.phase_timer)
                if flash_intensity > 15:
                    pyxel.rect(0, 0, pyxel.width, pyxel.height, 8)
    
    def get_displayed_life(self, character, initial_life, character_type):
        """戦闘の進行に応じて表示するライフ値を計算"""
        if self.phase == "intro":
            # 戦闘開始前のライフを表示
            return initial_life
        elif self.phase == "player_attack" and character_type == "enemy":
            # プレイヤー攻撃フェーズ中の敵のライフは徐々に減る
            if self.phase_timer < 60:  # 2秒間で減少
                progress = self.phase_timer / 60
                damage_taken = initial_life - character.life
                return int(initial_life - damage_taken * progress)
            else:
                return character.life
        elif self.phase == "enemy_attack" and character_type == "player":
            # 敵攻撃フェーズ中のプレイヤーのライフは徐々に減る
            if self.phase_timer < 60:  # 2秒間で減少
                progress = self.phase_timer / 60
                damage_taken = initial_life - character.life
                return int(initial_life - damage_taken * progress)
            else:
                return character.life
        else:
            # その他の場合は現在のライフを表示
            return character.life
