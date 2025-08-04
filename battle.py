import pyxel

from battle_states import BattleIntroState
from game import Scene
from map_state_machine import StateContext


class BattleScene(Scene):
    def __init__(self, city_id: int, game_state, previous_scene):
        super().__init__()
        self.city_id = city_id
        self.game_state = game_state  # GameStateの共有参照
        self.previous_scene = previous_scene  # 戻り先のシーン
        self.city = game_state.get_city_by_id(city_id)
        self.animation_timer = 0
        self.max_animation_time = 240  # 8秒間（30fps * 8秒）

        # 状態マシンの初期化
        self.state_context = StateContext()
        self.early_exit = False  # 早期終了フラグ
        self.battle_completed = False  # 戦闘完了フラグ

        self.damage_numbers = []  # ダメージ表示用

        # 戦闘に参加するキャラクター（GameStateから直接参照）
        self.battle_players, self.battle_enemies = game_state.get_characters_in_city(
            city_id
        )

        # 戦闘開始時のライフを記録（表示用）
        self.initial_player_lives = [p.life for p in self.battle_players]
        self.initial_enemy_lives = [e.life for e in self.battle_enemies]

        # イニシアチブ順序管理
        self.initiative_order = []
        self.current_attacker_index = 0
        self.current_attacker = None
        self.current_attack_damage = 0

        # イニシアチブ順を計算
        self.calculate_initiative_order()

        # 初期状態を設定
        self.state_context.change_state(BattleIntroState(self))

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
        self.initiative_order = sorted(
            all_characters, key=lambda c: c.initiative, reverse=True
        )
        self.current_attacker_index = 0

    def setup_next_attacker(self):
        """次の攻撃者を設定"""
        if self.current_attacker_index >= len(self.initiative_order):
            return False  # 全ての攻撃が完了

        self.current_attacker = self.initiative_order[self.current_attacker_index]
        self.current_attacker_index += 1
        return True

    def execute_attack(self):
        """現在の攻撃者で攻撃を実行し、GameStateを直接更新"""
        if not self.current_attacker or self.current_attacker.life <= 0:
            return 0

        damage = 0
        if self.current_attacker in self.battle_players:
            # プレイヤーの攻撃
            alive_enemies = [e for e in self.battle_enemies if e.life > 0]
            if alive_enemies:
                target = min(alive_enemies, key=lambda e: e.life)
                damage = min(self.current_attacker.attack, target.life)
                target.life = max(0, target.life - damage)

                # ダメージ表示
                if damage > 0:
                    self.add_damage_number(damage, "player")
        else:
            # 敵の攻撃
            alive_players = [p for p in self.battle_players if p.life > 0]
            if alive_players:
                target = min(alive_players, key=lambda p: p.life)
                damage = min(self.current_attacker.attack, target.life)
                target.life = max(0, target.life - damage)

                # ダメージ表示
                if damage > 0:
                    self.add_damage_number(damage, "enemy")

        self.current_attack_damage = damage
        return damage

    def update(self):
        self.animation_timer += 1

        # 早期終了チェック
        if self.early_exit:
            # 戦闘を早期終了して前のシーンに戻る
            return self.previous_scene

        # 状態マシンの更新
        result = self.state_context.update()
        if result is None:
            # 戦闘完了、前のシーンに戻る
            self.battle_completed = True
            return self.previous_scene

        # 入力処理
        self.state_context.handle_input()

        # ダメージナンバーの更新
        self.damage_numbers = [
            (damage, attacker, timer - 1)
            for damage, attacker, timer in self.damage_numbers
            if timer > 0
        ]

        # 現在のシーンを継続
        return self

    def add_damage_number(self, damage, attacker):
        """ダメージ数値を追加"""
        self.damage_numbers.append((damage, attacker, 90))  # 3秒間表示

    def draw(self):
        """メイン描画メソッド - 共通描画と状態固有描画を分離"""
        # 共通背景描画
        self.draw_background()
        
        # キャラクター描画
        self.draw_battle_characters()
        
        # 状態固有の描画を委譲
        self.draw_phase_content()
        
        # 共通UI要素
        self.draw_damage_numbers()
        self.draw_progress_bar()
        self.draw_skip_instruction()

    def draw_background(self):
        """背景とエフェクト描画"""
        # 半透明の黒い背景
        pyxel.rect(0, 0, pyxel.width, pyxel.height, 0)
        
        # フラッシュエフェクトを最初に描画（背景の上、他の要素の下）
        self.draw_flash_effects()

    def draw_phase_content(self):
        """フェーズ固有のコンテンツ描画 - 状態に委譲"""
        # 都市名表示（共通）
        info_x = pyxel.width // 2
        info_y = 60
        city_text = f"BATTLE AT {self.city.name}"
        text_width = len(city_text) * 4
        pyxel.text(info_x - text_width // 2, info_y - 30, city_text, 7)
        
        # 現在の状態に描画を委譲
        current_state = self.state_context.current_state
        if hasattr(current_state, 'draw_phase'):
            current_state.draw_phase()
        # フォールバック削除 - 全ての状態にdraw_phase()を実装済み

    def draw_damage_numbers(self):
        """ダメージナンバーの描画"""
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

    def draw_progress_bar(self):
        """プログレスバーの描画"""
        progress = min(1.0, self.animation_timer / self.max_animation_time)
        bar_width = pyxel.width - 40
        bar_x = 20
        bar_y = pyxel.height - 20

        # プログレスバーの背景
        pyxel.rect(bar_x, bar_y, bar_width, 4, 5)
        # プログレスバーの進行状況
        pyxel.rect(bar_x, bar_y, int(bar_width * progress), 4, 10)

    def draw_skip_instruction(self):
        """スキップ指示の描画"""
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
                    player, draw_x, draw_y, False, initial_life, "player"
                )  # 左向き

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
                    enemy, draw_x, draw_y, True, initial_life, "enemy"
                )  # 右向き

                # 敵名を表示
                name_text = f"Enemy {i+1}"
                pyxel.text(draw_x + 20, draw_y - 25, name_text, 8)

                # AI種別を表示
                ai_text = f"({enemy.ai_type})"
                pyxel.text(draw_x + 20, draw_y - 15, ai_text, 6)

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

        if (
            current_phase == "individual_attack"
            and hasattr(self, "current_attacker")
            and self.current_attacker
        ):
            if (
                character == self.current_attacker
                and current_state
                and current_state.get_elapsed_time() < 20
            ):
                # 攻撃時は少し前に出る
                offset_x = 5 if not facing_right else -5
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

        if (
            current_phase == "individual_attack"
            and hasattr(self, "current_attacker")
            and self.current_attacker
        ):
            if (
                current_state
                and current_state.get_elapsed_time() < 30
                and self.current_attack_damage > 0
            ):
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
