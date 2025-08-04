from abc import ABC, abstractmethod
from enum import Enum

import pyxel


class MapStateType(Enum):
    """マップシーンの状態タイプ"""

    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    ENEMY_SELECTION = "enemy_selection"  # 敵選択演出状態を追加
    TRANSITION = "transition"
    BATTLE_SEQUENCE = "battle_sequence"
    CITY_DISCOVERY = "city_discovery"  # 都市発見表示状態を追加
    CUTIN = "cutin"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    PAUSED = "paused"


class BattleStateType(Enum):
    """戦闘シーンの状態タイプ"""

    INTRO = "intro"
    INDIVIDUAL_ATTACK = "individual_attack"  # 個別攻撃フェーズ
    RESULTS = "results"
    OUTRO = "outro"


class MapGameState(ABC):
    """マップゲーム状態の基底クラス"""

    def __init__(self, context, state_type: MapStateType):
        self.context = context  # MapSceneへの参照
        self.state_type = state_type
        self.enter_time = 0  # 状態に入った時間

    @abstractmethod
    def enter(self):
        """状態開始時の処理"""
        self.enter_time = pyxel.frame_count

    @abstractmethod
    def update(self):
        """毎フレーム更新処理
        Returns:
            Scene: 継続する場合はself、シーン変更の場合は新しいシーン、終了の場合はNone
        """
        pass

    @abstractmethod
    def handle_input(self):
        """入力処理"""
        pass

    @abstractmethod
    def exit(self):
        """状態終了時の処理"""
        pass

    def transition_to(self, new_state):
        """状態遷移実行"""
        self.context.change_state(new_state)

    def get_elapsed_time(self):
        """状態に入ってからの経過時間（フレーム数）"""
        return pyxel.frame_count - self.enter_time


class BattleGameState(ABC):
    """戦闘ゲーム状態の基底クラス"""

    def __init__(self, context, state_type: BattleStateType):
        self.context = context  # BattleSubSceneへの参照
        self.state_type = state_type
        self.enter_time = 0  # 状態に入った時間

    @abstractmethod
    def enter(self):
        """状態開始時の処理"""
        self.enter_time = pyxel.frame_count
        print(f"[ENTER] battle {self.state_type.value}")

    @abstractmethod
    def update(self):
        """毎フレーム更新処理
        Returns:
            Scene: 継続する場合はself、終了の場合はNone
        """
        pass

    @abstractmethod
    def handle_input(self):
        """入力処理"""
        pass

    @abstractmethod
    def exit(self):
        """状態終了時の処理"""
        print(f"[EXIT] battle {self.state_type.value}")
        pass

    def transition_to(self, new_state):
        """状態遷移実行"""
        self.context.change_state(new_state)

    def get_elapsed_time(self):
        """状態に入ってからの経過時間（フレーム数）"""
        return pyxel.frame_count - self.enter_time

    def draw_battle_characters(self):
        """戦闘キャラクターの描画（各状態でオーバーライド可能）"""
        # プレイヤーキャラクターを左側に描画
        player_start_x = 50
        player_y = pyxel.height // 2 + 20

        for i, player in enumerate(self.context.battle_players):
            # プレイヤーの描画位置（縦に並べる）
            draw_x = player_start_x
            draw_y = player_y + i * 40  # 40ピクセル間隔で縦に配置

            # プレイヤーが画面内に収まるかチェック
            if draw_y + player.height < pyxel.height - 20:
                initial_life = self.context.initial_player_lives[i]
                self.draw_character(
                    player, draw_x, draw_y, True, initial_life, "player"
                )  # 右向き

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
            # 敵の描画位置（縦に並べる）
            draw_x = enemy_start_x
            draw_y = enemy_y + i * 40  # 40ピクセル間隔で縦に配置

            # 敵が画面内に収まるかチェック
            if draw_y + enemy.height < pyxel.height - 20:
                initial_life = self.context.initial_enemy_lives[i]
                self.draw_character(
                    enemy, draw_x, draw_y, False, initial_life, "enemy"
                )  # 左向き

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

    def draw_character(self, character, x, y, facing_right, initial_life, character_type):
        """キャラクターを指定位置に描画（各状態でオーバーライド可能）"""
        half_width = character.width // 2
        half_height = character.height // 2

        # アニメーションフレームを計算（戦闘中はゆっくりとしたアニメーション）
        anim_frame = (pyxel.frame_count // 20) % 2
        src_x = anim_frame * 16
        src_y = character.image_index * 16

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
        displayed_life = self.context.get_displayed_life(
            character, initial_life, character_type
        )

        # ライフゲージの現在値（緑色）
        current_life_width = int((displayed_life / character.max_life) * life_bar_width)
        if current_life_width > 0:
            pyxel.rect(life_bar_x, life_bar_y, current_life_width, life_bar_height, 11)


class StateContext:
    """状態管理コンテキスト"""

    def __init__(self):
        self.current_state = None
        self.previous_state = None
        self.state_history = []  # デバッグ用状態履歴

    def change_state(self, new_state):
        """状態を変更"""
        if self.current_state:
            self.current_state.exit()
            self.previous_state = self.current_state

        # 状態履歴を記録（最新10件まで）
        if len(self.state_history) >= 10:
            self.state_history.pop(0)
        self.state_history.append(
            {
                "from": self.current_state.state_type if self.current_state else None,
                "to": new_state.state_type,
                "time": pyxel.frame_count,
            }
        )

        self.current_state = new_state
        new_state.enter()

    def update(self):
        """現在の状態を更新"""
        if self.current_state:
            return self.current_state.update()
        return None

    def handle_input(self):
        """現在の状態の入力処理"""
        if self.current_state:
            self.current_state.handle_input()

    def get_current_state_type(self):
        """現在の状態タイプを取得"""
        return self.current_state.state_type if self.current_state else None

    def draw_debug_info(self, x, y):
        """デバッグ情報を描画"""
        if self.current_state:
            current_type = self.current_state.state_type.value
            elapsed = self.current_state.get_elapsed_time()
            pyxel.text(x, y, f"State: {current_type} ({elapsed}f)", 7)

            # 状態履歴を表示
            for i, history in enumerate(self.state_history[-3:]):  # 最新3件
                from_state = history["from"].value if history["from"] else "None"
                to_state = history["to"].value
                pyxel.text(x, y + 10 + i * 8, f"  {from_state} -> {to_state}", 6)
