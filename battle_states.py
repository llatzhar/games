import pyxel

from map_state_machine import BattleGameState, BattleStateType


class BattleIntroState(BattleGameState):
    """戦闘開始演出状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.INTRO)

    def enter(self):
        super().enter()
        # イニシアチブ順を計算（既に__init__で実行済み）

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, "early_exit") and self.context.early_exit:
            return None

        # 2秒経過で次のフェーズに遷移
        if self.get_elapsed_time() >= 60:  # 2秒
            self.transition_to(BattleIndividualAttackState(self.context))
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def draw_phase(self):
        """戦闘開始フェーズ固有の描画"""
        # キャラクター描画
        self.draw_battle_characters()
        
        # バトル開始メッセージ
        msg_x = 160 - (len("Battle Start!") * 4) // 2
        pyxel.text(msg_x, 120, "Battle Start!", 8)
        
        # イニシアチブ順表示
        y_offset = 140
        for i, character in enumerate(self.context.initiative_order):
            # キャラクターの種類を判定
            if hasattr(character, 'ai_type'):
                # Enemy
                char_name = f"{character.ai_type.capitalize()} Enemy"
            else:
                # Player
                char_name = "Player"
            
            text = f"{i+1}. {char_name} (Init: {character.initiative})"
            pyxel.text(10, y_offset + i * 8, text, 7)

    def exit(self):
        super().exit()
        pass


class BattleIndividualAttackState(BattleGameState):
    """個別攻撃フェーズ状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.INDIVIDUAL_ATTACK)
        # アニメーション管理
        self.animation_phase = "approach"  # approach, attack, return
        self.attacker_start_pos = None
        self.attacker_target_pos = None
        self.attack_start_time = 0

    def enter(self):
        super().enter()
        # 次の攻撃者を設定
        if not self.context.setup_next_attacker():
            # 全ての攻撃が完了した場合
            self.transition_to(BattleResultsState(self.context))
            return

        # 攻撃アニメーション用の位置計算
        self.setup_attack_animation()

        # 攻撃を実行してGameStateを更新
        self.context.execute_attack()

    def setup_attack_animation(self):
        """攻撃アニメーションの初期設定"""
        if not self.context.current_attacker:
            return
            
        # 攻撃者の初期位置を計算
        if self.context.current_attacker in self.context.battle_players:
            # プレイヤーの位置
            player_index = self.context.battle_players.index(self.context.current_attacker)
            self.attacker_start_pos = (50, pyxel.height // 2 + 20 + player_index * 40)
            # 敵側への攻撃位置（敵の少し手前）
            self.attacker_target_pos = (pyxel.width - 120, self.attacker_start_pos[1])
        else:
            # 敵の位置
            enemy_index = self.context.battle_enemies.index(self.context.current_attacker)
            self.attacker_start_pos = (pyxel.width - 80, pyxel.height // 2 + 20 + enemy_index * 40)
            # プレイヤー側への攻撃位置（プレイヤーの少し手前）
            self.attacker_target_pos = (90, self.attacker_start_pos[1])

    def get_attacker_animated_position(self):
        """放物線アニメーションによる攻撃者の現在位置を計算"""
        if not self.attacker_start_pos or not self.attacker_target_pos:
            return self.attacker_start_pos
            
        elapsed = self.get_elapsed_time()
        
        if self.animation_phase == "approach":
            # 接近フェーズ（0-20フレーム）
            if elapsed < 20:
                progress = elapsed / 20.0
                # 放物線の軌道計算
                start_x, start_y = self.attacker_start_pos
                target_x, target_y = self.attacker_target_pos
                
                # X軸は線形補間
                current_x = start_x + (target_x - start_x) * progress
                # Y軸は放物線（上に弧を描く）
                arc_height = 30  # 弧の高さ
                arc_progress = 4 * progress * (1 - progress)  # 0-1-0の放物線
                current_y = start_y + (target_y - start_y) * progress - arc_height * arc_progress
                
                return (current_x, current_y)
            else:
                self.animation_phase = "attack"
                self.attack_start_time = elapsed
                return self.attacker_target_pos
                
        elif self.animation_phase == "attack":
            # 攻撃フェーズ（20-30フレーム）
            if elapsed < 30:
                return self.attacker_target_pos
            else:
                self.animation_phase = "return"
                return self.attacker_target_pos
                
        elif self.animation_phase == "return":
            # 帰還フェーズ（30-50フレーム）
            if elapsed < 50:
                progress = (elapsed - 30) / 20.0
                # 直線で元の位置に戻る
                target_x, target_y = self.attacker_target_pos
                start_x, start_y = self.attacker_start_pos
                
                current_x = target_x + (start_x - target_x) * progress
                current_y = target_y + (start_y - target_y) * progress
                
                return (current_x, current_y)
            else:
                return self.attacker_start_pos
        
        return self.attacker_start_pos

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, "early_exit") and self.context.early_exit:
            return None

        # アニメーション完了後（50フレーム）で次の攻撃者に移行
        if self.get_elapsed_time() >= 50:
            # 次の攻撃者がいるかチェック
            if self.context.current_attacker_index < len(self.context.initiative_order):
                # 次の攻撃者がいる場合、新しい攻撃状態を開始
                self.transition_to(BattleIndividualAttackState(self.context))
            else:
                # 全ての攻撃が完了
                self.transition_to(BattleResultsState(self.context))
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def draw_phase(self):
        """個別攻撃フェーズ固有の描画"""
        # キャラクター描画（アニメーション付き）
        self.draw_battle_characters()
        
        # 現在の攻撃者情報
        if hasattr(self.context, 'current_attacker') and self.context.current_attacker:
            attacker = self.context.current_attacker
            
            # 攻撃者の種類を判定
            if hasattr(attacker, 'ai_type'):
                # Enemy
                attacker_name = f"{attacker.ai_type.capitalize()} Enemy"
            else:
                # Player
                attacker_name = "Player"
            
            # 攻撃者名表示
            msg = f"{attacker_name} attacks!"
            msg_x = 160 - (len(msg) * 4) // 2
            pyxel.text(msg_x, 100, msg, 8)

    def draw_battle_characters(self):
        """アニメーション付きキャラクター描画"""
        # プレイヤーキャラクターを左側に描画
        player_start_x = 50
        player_y = pyxel.height // 2 + 20

        for i, player in enumerate(self.context.battle_players):
            # 攻撃中のキャラクターは元の位置では描画しない
            if player == self.context.current_attacker and self.attacker_start_pos:
                continue
                
            # プレイヤーの描画位置（縦に並べる）
            draw_x = player_start_x
            draw_y = player_y + i * 40  # 40ピクセル間隔で縦に配置

            # プレイヤーが画面内に収まるかチェック
            if draw_y + player.height < pyxel.height - 20:
                initial_life = self.context.initial_player_lives[i]
                self.draw_character(
                    player, draw_x, draw_y, True, initial_life, "player"
                )  # 右向き（敵の方を向く）

                # プレイヤー名を表示
                name_text = f"Player {i+1}"
                pyxel.text(draw_x - len(name_text) * 2, draw_y - 25, name_text, 11)

                # ライフ表示（戦闘の進行に応じて変化）
                displayed_life = self.context.get_displayed_life(player, initial_life, "player")
                life_text = f"HP: {displayed_life}/{player.max_life}"
                pyxel.text(draw_x - len(life_text) * 2, draw_y - 15, life_text, 7)

        # 敵キャラクターを右側に描画
        enemy_start_x = pyxel.width - 80
        enemy_y = pyxel.height // 2 + 20

        for i, enemy in enumerate(self.context.battle_enemies):
            # 攻撃中のキャラクターは元の位置では描画しない
            if enemy == self.context.current_attacker and self.attacker_start_pos:
                continue
                
            # 敵の描画位置（縦に並べる）
            draw_x = enemy_start_x
            draw_y = enemy_y + i * 40  # 40ピクセル間隔で縦に配置

            # 敵が画面内に収まるかチェック
            if draw_y + enemy.height < pyxel.height - 20:
                initial_life = self.context.initial_enemy_lives[i]
                self.draw_character(
                    enemy, draw_x, draw_y, False, initial_life, "enemy"
                )  # 左向き（プレイヤーの方を向く）

                # 敵名を表示
                name_text = f"Enemy {i+1}"
                pyxel.text(draw_x + 20, draw_y - 25, name_text, 8)

                # AI種別を表示
                ai_text = f"({enemy.ai_type})"
                pyxel.text(draw_x + 20, draw_y - 15, ai_text, 6)

                # ライフ表示（戦闘の進行に応じて変化）
                displayed_life = self.context.get_displayed_life(
                    enemy, self.context.initial_enemy_lives[i], "enemy"
                )
                life_text = f"HP: {displayed_life}/{enemy.max_life}"
                pyxel.text(draw_x + 20, draw_y - 5, life_text, 7)
        
        # 攻撃中のキャラクターをアニメーション位置で描画
        if self.context.current_attacker and self.attacker_start_pos:
            # 攻撃者のインデックスを特定
            if self.context.current_attacker in self.context.battle_players:
                attacker_index = self.context.battle_players.index(self.context.current_attacker)
                initial_life = self.context.initial_player_lives[attacker_index]
                character_type = "player"
                facing_right = True
            else:
                attacker_index = self.context.battle_enemies.index(self.context.current_attacker)
                initial_life = self.context.initial_enemy_lives[attacker_index]
                character_type = "enemy"
                facing_right = False
            
            # アニメーション位置を取得
            anim_x, anim_y = self.get_attacker_animated_position()
            
            # 攻撃者をアニメーション位置で描画
            self.draw_character(
                self.context.current_attacker, 
                anim_x, anim_y, 
                facing_right, 
                initial_life, 
                character_type
            )
            
            # 攻撃者の名前とライフを表示（アニメーション位置に追従）
            if self.context.current_attacker in self.context.battle_players:
                attacker_index = self.context.battle_players.index(self.context.current_attacker)
                name_text = f"Player {attacker_index+1}"
                pyxel.text(int(anim_x) - len(name_text) * 2, int(anim_y) - 25, name_text, 11)
                
                displayed_life = self.context.get_displayed_life(self.context.current_attacker, initial_life, "player")
                life_text = f"HP: {displayed_life}/{self.context.current_attacker.max_life}"
                pyxel.text(int(anim_x) - len(life_text) * 2, int(anim_y) - 15, life_text, 7)
            else:
                attacker_index = self.context.battle_enemies.index(self.context.current_attacker)
                name_text = f"Enemy {attacker_index+1}"
                pyxel.text(int(anim_x) + 20, int(anim_y) - 25, name_text, 8)
                
                ai_text = f"({self.context.current_attacker.ai_type})"
                pyxel.text(int(anim_x) + 20, int(anim_y) - 15, ai_text, 6)
                
                displayed_life = self.context.get_displayed_life(self.context.current_attacker, initial_life, "enemy")
                life_text = f"HP: {displayed_life}/{self.context.current_attacker.max_life}"
                pyxel.text(int(anim_x) + 20, int(anim_y) - 5, life_text, 7)

    def exit(self):
        super().exit()
        pass


class BattleResultsState(BattleGameState):
    """戦闘結果表示状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.RESULTS)

    def enter(self):
        super().enter()

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, "early_exit") and self.context.early_exit:
            return None

        # 3秒経過で次のフェーズに遷移
        if self.get_elapsed_time() >= 90:  # 3秒
            self.transition_to(BattleOutroState(self.context))
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def draw_phase(self):
        """戦闘結果フェーズ固有の描画"""
        # キャラクター描画
        self.draw_battle_characters()
        
        # 戦闘結果表示
        pyxel.text(120, 100, "Battle Results", 8)
        
        # ダメージ結果表示
        if hasattr(self.context, 'battle_results') and self.context.battle_results:
            y_offset = 120
            for result in self.context.battle_results[:5]:  # 最大5件表示
                damage_text = f"Damage: {result.get('damage', 0)}"
                pyxel.text(10, y_offset, damage_text, 7)
                y_offset += 10
        else:
            pyxel.text(10, 120, "No damage dealt", 6)

    def exit(self):
        super().exit()
        pass


class BattleOutroState(BattleGameState):
    """戦闘終了演出状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.OUTRO)

    def enter(self):
        super().enter()

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, "early_exit") and self.context.early_exit:
            return None

        # 1秒経過で戦闘終了
        if self.get_elapsed_time() >= 30:  # 1秒
            self.exit()
            return None  # サブシーン終了
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def draw_phase(self):
        """戦闘終了フェーズ固有の描画"""
        # キャラクター描画
        self.draw_battle_characters()
        
        # 戦闘終了メッセージ
        msg = "Battle Complete!"
        msg_x = 160 - (len(msg) * 4) // 2
        pyxel.text(msg_x, 120, msg, 11)
        
        # フェードアウト効果（時間経過で薄くなる）
        progress = self.get_elapsed_time() / 30.0
        if progress > 0.5:
            fade_alpha = int((1.0 - progress) * 255)
            # Pyxelには直接のアルファブレンドがないので、色の明度で表現
            fade_color = 1 if progress > 0.8 else 5
            pyxel.text(msg_x, 140, "Returning to map...", fade_color)

    def exit(self):
        super().exit()
        pass
