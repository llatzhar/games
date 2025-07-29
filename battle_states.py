import pyxel

from map_state_machine import BattleGameState, BattleStateType


class BattleIntroState(BattleGameState):
    """戦闘開始演出状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.INTRO)

    def enter(self):
        super().enter()
        # 戦闘開始時の状態をキャプチャ
        self.context.capture_initial_state()

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, 'early_exit') and self.context.early_exit:
            return None
            
        # 2秒経過で次のフェーズに遷移
        if self.get_elapsed_time() >= 60:  # 2秒
            self.transition_to(BattlePlayerAttackState(self.context))
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def exit(self):
        pass


class BattlePlayerAttackState(BattleGameState):
    """プレイヤー攻撃フェーズ状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.PLAYER_ATTACK)

    def enter(self):
        super().enter()
        # プレイヤーダメージ数値を追加
        if self.context.player_damage > 0:
            self.context.add_damage_number(self.context.player_damage, "player")

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, 'early_exit') and self.context.early_exit:
            return None
            
        # 2秒経過で次のフェーズに遷移
        if self.get_elapsed_time() >= 60:  # 2秒
            self.transition_to(BattleEnemyAttackState(self.context))
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def exit(self):
        pass


class BattleEnemyAttackState(BattleGameState):
    """敵攻撃フェーズ状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.ENEMY_ATTACK)

    def enter(self):
        super().enter()
        # 敵ダメージ数値を追加
        if self.context.enemy_damage > 0:
            self.context.add_damage_number(self.context.enemy_damage, "enemy")

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, 'early_exit') and self.context.early_exit:
            return None
            
        # 2秒経過で次のフェーズに遷移
        if self.get_elapsed_time() >= 60:  # 2秒
            self.transition_to(BattleResultsState(self.context))
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def exit(self):
        pass


class BattleResultsState(BattleGameState):
    """戦闘結果表示状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.RESULTS)

    def enter(self):
        super().enter()

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, 'early_exit') and self.context.early_exit:
            return None
            
        # 3秒経過で次のフェーズに遷移
        if self.get_elapsed_time() >= 90:  # 3秒
            self.transition_to(BattleOutroState(self.context))
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def exit(self):
        pass


class BattleOutroState(BattleGameState):
    """戦闘終了演出状態"""

    def __init__(self, context):
        super().__init__(context, BattleStateType.OUTRO)

    def enter(self):
        super().enter()

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, 'early_exit') and self.context.early_exit:
            return None
            
        # 1秒経過で戦闘終了
        if self.get_elapsed_time() >= 30:  # 1秒
            return None  # サブシーン終了
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def exit(self):
        pass
