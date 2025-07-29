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
        if hasattr(self.context, 'early_exit') and self.context.early_exit:
            return None
            
        # 2秒経過で次のフェーズに遷移
        if self.get_elapsed_time() >= 60:  # 2秒
            self.transition_to(BattleIndividualAttackState(self.context))
        return self.context

    def handle_input(self):
        # ESCまたはスペースで早期終了
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_SPACE):
            self.context.early_exit = True

    def exit(self):
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
        else:
            # 攻撃を実行してGameStateを更新
            self.context.execute_attack()

    def update(self):
        # 早期終了チェック
        if hasattr(self.context, 'early_exit') and self.context.early_exit:
            return None
            
        # 2秒経過で次の攻撃者に移行
        if self.get_elapsed_time() >= 60:  # 2秒
            if self.context.setup_next_attacker():
                # 次の攻撃者がいる場合、状態を再開始
                self.transition_to(BattleIndividualAttackState(self.context))
            else:
                # 全ての攻撃が完了
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
