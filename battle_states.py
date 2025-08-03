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

    def enter(self):
        super().enter()
        # 次の攻撃者を設定
        if not self.context.setup_next_attacker():
            # 全ての攻撃が完了した場合
            self.transition_to(BattleResultsState(self.context))
            return

        # 攻撃を実行してGameStateを更新
        self.context.execute_attack()

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, "early_exit") and self.context.early_exit:
            return None

        # 2秒経過で次の攻撃者に移行
        if self.get_elapsed_time() >= 60:  # 2秒
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
            
            # 攻撃進行表示
            progress = min(self.get_elapsed_time() / 60.0, 1.0)
            bar_width = int(120 * progress)
            pyxel.rect(100, 130, bar_width, 8, 10)
            pyxel.rectb(100, 130, 120, 8, 7)

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
