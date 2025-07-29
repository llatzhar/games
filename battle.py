import pyxel

from game import SubScene
from map_state_machine import StateContext, BattleStateType
from battle_states import BattleIntroState


class BattleSubScene(SubScene):
    def __init__(self, parent_scene, battle_info, city):
        super().__init__(parent_scene)
        self.battle_info = battle_info  # 戦闘場所情報（まだ戦闘は実行されていない）
        self.city = city
        self.animation_timer = 0
        self.max_animation_time = 240  # 8秒間（30fps * 8秒）
        
        # 状態マシンの初期化
        self.state_context = StateContext()
        self.early_exit = False  # 早期終了フラグ
        
        self.damage_numbers = []  # ダメージ表示用

        # 戦闘に参加するキャラクター（戦闘開始時の状態をキャプチャ）
        self.battle_players = battle_info["players"]
        self.battle_enemies = battle_info["enemies"]

        # 戦闘開始時のライフを記録（戦闘前の状態を保存）
        self.initial_player_lives = []
        self.initial_enemy_lives = []

        # 戦闘計算を実行（ここで初めて実際の戦闘を行う）
        self.battle_result = self.execute_battle()

        # 戦闘ログから情報を抽出
        self.parse_battle_log()
        
        # イニシアチブ順序管理
        self.initiative_order = []
        self.current_attacker_index = 0
        self.current_attacker = None
        self.current_attack_damage = 0
        
        # 初期状態を設定
        self.state_context.change_state(BattleIntroState(self))

    def capture_initial_state(self):
        """戦闘開始時の状態をキャプチャ"""
        self.initial_player_lives = [p.life for p in self.battle_players]
        self.initial_enemy_lives = [e.life for e in self.battle_enemies]

    def change_state(self, new_state):
        """状態変更（状態マシンとの連携）"""
        self.state_context.change_state(new_state)

    def get_current_phase(self):
        """現在のフェーズを取得"""
        current_state = self.state_context.current_state
        if current_state:
            return current_state.state_type.value
        return "unknown"

    def calculate_initiative_order(self):
        """イニシアチブ順を計算"""
        all_characters = self.battle_players + self.battle_enemies
        self.initiative_order = sorted(all_characters, key=lambda c: c.initiative, reverse=True)
        self.current_attacker_index = 0

    def setup_next_attacker(self):
        """次の攻撃者を設定"""
        if self.current_attacker_index >= len(self.initiative_order):
            return False  # 全ての攻撃が完了
            
        self.current_attacker = self.initiative_order[self.current_attacker_index]
        
        # 戦闘ログから該当する攻撃のダメージを取得
        self.current_attack_damage = self.get_damage_for_attacker(self.current_attacker)
        
        # ダメージ数値を表示
        if self.current_attack_damage > 0:
            attacker_type = "player" if self.current_attacker in self.battle_players else "enemy"
            self.add_damage_number(self.current_attack_damage, attacker_type)
        
        self.current_attacker_index += 1
        return True

    def get_damage_for_attacker(self, attacker):
        """特定の攻撃者のダメージを戦闘ログから取得"""
        for log_entry in self.battle_result["log"]:
            if attacker in self.battle_players:
                # プレイヤーの攻撃を探す
                if f"Player (Init:{attacker.initiative})" in log_entry:
                    parts = log_entry.split()
                    for i, part in enumerate(parts):
                        if part == "dealt" and i + 1 < len(parts):
                            try:
                                return int(parts[i + 1])
                            except ValueError:
                                pass
            else:
                # 敵の攻撃を探す
                if f"{attacker.ai_type} enemy (Init:{attacker.initiative})" in log_entry:
                    parts = log_entry.split()
                    for i, part in enumerate(parts):
                        if part == "dealt" and i + 1 < len(parts):
                            try:
                                return int(parts[i + 1])
                            except ValueError:
                                pass
        return 0

    def execute_battle(self):
        """戦闘を実行して結果を返す（イニシアチブ順）"""
        battle_log = []
        city_name = self.city.name

        # 全キャラクターをイニシアチブ順にソート
        all_characters = self.battle_players + self.battle_enemies
        sorted_characters = sorted(all_characters, key=lambda c: c.initiative, reverse=True)
        
        # イニシアチブ順で攻撃処理
        for attacker in sorted_characters:
            if attacker.life <= 0:
                continue  # 既に倒されている場合はスキップ
                
            if attacker in self.battle_players:
                # プレイヤーの攻撃
                if self.battle_enemies:
                    # 生きている敵の中で最も弱い敵を攻撃
                    alive_enemies = [e for e in self.battle_enemies if e.life > 0]
                    if alive_enemies:
                        target_enemy = min(alive_enemies, key=lambda e: e.life)
                        damage = min(attacker.attack, target_enemy.life)
                        target_enemy.life -= damage
                        battle_log.append(
                            f"Player (Init:{attacker.initiative}) dealt {damage} damage to {target_enemy.ai_type} enemy (Init:{target_enemy.initiative}) in {city_name}"
                        )
            else:
                # 敵の攻撃
                if self.battle_players:
                    # 生きているプレイヤーの中で最も弱いプレイヤーを攻撃
                    alive_players = [p for p in self.battle_players if p.life > 0]
                    if alive_players:
                        target_player = min(alive_players, key=lambda p: p.life)
                        damage = min(attacker.attack, target_player.life)
                        target_player.life -= damage
                        battle_log.append(
                            f"{attacker.ai_type} enemy (Init:{attacker.initiative}) dealt {damage} damage to player (Init:{target_player.initiative}) in {city_name}"
                        )

        return {
            "city_id": self.city.id,
            "log": battle_log,
            "players_before": len(self.battle_players),
            "enemies_before": len(self.battle_enemies),
        }

    def parse_battle_log(self):
        """戦闘ログから表示用の情報を抽出（イニシアチブベース）"""
        self.player_damage = 0
        self.enemy_damage = 0
        self.target_enemy_type = "enemy"

        for log_entry in self.battle_result["log"]:
            if "Player (Init:" in log_entry:
                # "Player (Init:15) dealt 25 damage to aggressive enemy (Init:12) in Town A"
                parts = log_entry.split()
                damage_index = -1
                for i, part in enumerate(parts):
                    if part == "dealt" and i + 1 < len(parts):
                        try:
                            self.player_damage += int(parts[i + 1])
                        except ValueError:
                            pass
                        break
                        
                # 敵タイプを特定
                if "aggressive" in log_entry:
                    self.target_enemy_type = "aggressive"
                elif "patrol" in log_entry:
                    self.target_enemy_type = "patrol"
                elif "defensive" in log_entry:
                    self.target_enemy_type = "defensive"
                elif "random" in log_entry:
                    self.target_enemy_type = "random"

            elif "enemy (Init:" in log_entry:
                # "aggressive enemy (Init:12) dealt 20 damage to player (Init:15) in Town A"
                parts = log_entry.split()
                for i, part in enumerate(parts):
                    if part == "dealt" and i + 1 < len(parts):
                        try:
                            self.enemy_damage += int(parts[i + 1])
                        except ValueError:
                            pass
                        break

    def update(self):
        self.animation_timer += 1

        # 早期終了チェック
        if self.early_exit:
            return None

        # 状態マシンの更新
        result = self.state_context.update()
        if result is None:
            return None  # サブシーン終了

        # 入力処理
        self.state_context.handle_input()

        # ダメージナンバーの更新
        self.damage_numbers = [
            (damage, attacker, timer - 1)
            for damage, attacker, timer in self.damage_numbers
            if timer > 0
        ]

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
        current_phase = self.get_current_phase()
        
        if current_phase == "intro":
            intro_text = "Battle begins!"
            text_width = len(intro_text) * 4
            pyxel.text(info_x - text_width // 2, info_y, intro_text, 11)
            
            # イニシアチブ順を表示
            if hasattr(self, 'initiative_order') and self.initiative_order:
                order_text = "Initiative Order:"
                pyxel.text(info_x - len(order_text) * 2, info_y + 20, order_text, 6)
                for i, char in enumerate(self.initiative_order[:3]):  # 最初の3キャラまで表示
                    char_type = "Player" if char in self.battle_players else f"{char.ai_type} Enemy"
                    char_text = f"{char_type} (Init:{char.initiative})"
                    pyxel.text(info_x - len(char_text) * 2, info_y + 30 + i * 8, char_text, 7)

        elif current_phase == "individual_attack":
            if hasattr(self, 'current_attacker') and self.current_attacker:
                if self.current_attacker in self.battle_players:
                    attack_text = f"Player (Init:{self.current_attacker.initiative}) attacks for {self.current_attack_damage} damage!"
                    color = 11
                else:
                    attack_text = f"{self.current_attacker.ai_type} Enemy (Init:{self.current_attacker.initiative}) attacks for {self.current_attack_damage} damage!"
                    color = 8
                text_width = len(attack_text) * 4
                pyxel.text(info_x - text_width // 2, info_y, attack_text, color)

        elif current_phase == "results":
            result_text = "Battle concluded"
            text_width = len(result_text) * 4
            pyxel.text(info_x - text_width // 2, info_y, result_text, 10)

            # 戦闘前後の兵力表示
            players_count = self.battle_result["players_before"]
            enemies_count = self.battle_result["enemies_before"]
            battle_summary = f"Players: {players_count}, Enemies: {enemies_count}"
            summary_width = len(battle_summary) * 4
            pyxel.text(info_x - summary_width // 2, info_y + 20, battle_summary, 6)

        elif current_phase == "outro":
            # フェードアウト効果
            current_state = self.state_context.current_state
            fade_alpha = min(current_state.get_elapsed_time() * 8, 255) if current_state else 0
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
                initial_life = self.initial_player_lives[i]
                self.draw_character(
                    player, draw_x, draw_y, True, initial_life, "player"
                )  # 右向き

                # プレイヤー名を表示
                name_text = f"Player {i+1}"
                pyxel.text(draw_x - len(name_text) * 2, draw_y - 25, name_text, 11)

                # ライフ表示（戦闘の進行に応じて変化）
                initial_life = self.initial_player_lives[i]
                displayed_life = self.get_displayed_life(player, initial_life, "player")
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
                initial_life = self.initial_enemy_lives[i]
                self.draw_character(
                    enemy, draw_x, draw_y, False, initial_life, "enemy"
                )  # 左向き

                # 敵名を表示
                name_text = f"Enemy {i+1}"
                pyxel.text(draw_x + 20, draw_y - 25, name_text, 8)

                # AI種別を表示
                ai_text = f"({enemy.ai_type})"
                pyxel.text(draw_x + 20, draw_y - 15, ai_text, 6)

                # ライフ表示
                # ライフ表示（戦闘の進行に応じて変化）
                displayed_life = self.get_displayed_life(
                    enemy, self.initial_enemy_lives[i], "enemy"
                )
                life_text = f"HP: {displayed_life}/{enemy.max_life}"
                pyxel.text(draw_x + 20, draw_y - 5, life_text, 7)

    def draw_character(
        self, character, x, y, facing_right, initial_life, character_type
    ):
        """キャラクターを指定位置に描画"""
        half_width = character.width // 2
        half_height = character.height // 2

        # アニメーションフレームを計算（戦闘中はゆっくりとしたアニメーション）
        anim_frame = (pyxel.frame_count // 20) % 2
        src_x = anim_frame * 16
        src_y = character.image_index * 16

        # 攻撃フェーズ中は攻撃アニメーション
        current_phase = self.get_current_phase()
        current_state = self.state_context.current_state
        
        if current_phase == "individual_attack" and hasattr(self, 'current_attacker') and self.current_attacker:
            if character == self.current_attacker and current_state and current_state.get_elapsed_time() < 20:
                # 攻撃時は少し前に出る
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
            2,  # 透明色
        )

        # ライフゲージを描画（戦闘進行に応じた値を使用）
        life_bar_width = character.width
        life_bar_height = 3
        life_bar_x = int(x - half_width)
        life_bar_y = int(y - half_height - 10)

        # ライフゲージの背景（赤色）
        pyxel.rect(life_bar_x, life_bar_y, life_bar_width, life_bar_height, 8)

        # 戦闘進行に応じた表示ライフ値を取得
        displayed_life = self.get_displayed_life(
            character, initial_life, character_type
        )

        # ライフゲージの現在値（緑色）
        current_life_width = int((displayed_life / character.max_life) * life_bar_width)
        if current_life_width > 0:
            pyxel.rect(life_bar_x, life_bar_y, current_life_width, life_bar_height, 11)

    def draw_flash_effects(self):
        """フラッシュエフェクトを描画（背景の上、他の要素の下）"""
        current_phase = self.get_current_phase()
        current_state = self.state_context.current_state
        
        if current_phase == "individual_attack" and hasattr(self, 'current_attacker') and self.current_attacker:
            if current_state and current_state.get_elapsed_time() < 30 and self.current_attack_damage > 0:
                flash_intensity = max(0, 30 - current_state.get_elapsed_time())
                if flash_intensity > 15:
                    if self.current_attacker in self.battle_players:
                        # プレイヤー攻撃: 青色閃光
                        pyxel.rect(0, 0, pyxel.width, pyxel.height, 12)
                    else:
                        # 敵攻撃: 赤色閃光
                        pyxel.rect(0, 0, pyxel.width, pyxel.height, 8)

    def get_displayed_life(self, character, initial_life, character_type):
        """戦闘の進行に応じて表示するライフ値を計算"""
        current_phase = self.get_current_phase()
        current_state = self.state_context.current_state
        
        if current_phase == "intro":
            # 戦闘開始前のライフを表示
            return initial_life
        elif current_phase == "player_attack" and character_type == "enemy":
            # プレイヤー攻撃フェーズ中の敵のライフは徐々に減る
            if current_state and current_state.get_elapsed_time() < 60:  # 2秒間で減少
                progress = current_state.get_elapsed_time() / 60
                damage_taken = initial_life - character.life
                return int(initial_life - damage_taken * progress)
            else:
                return character.life
        elif current_phase == "enemy_attack" and character_type == "player":
            # 敵攻撃フェーズ中のプレイヤーのライフは徐々に減る
            if current_state and current_state.get_elapsed_time() < 60:  # 2秒間で減少
                progress = current_state.get_elapsed_time() / 60
                damage_taken = initial_life - character.life
                return int(initial_life - damage_taken * progress)
            else:
                return character.life
        else:
            # その他の場合は現在のライフを表示
            return character.life
