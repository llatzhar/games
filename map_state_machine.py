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
    PARABOLIC_MOTION = "parabolic_motion"
    DAMAGE_DISPLAY = "damage_display"
    DEATH_CHECK = "death_check"
    DEATH_ANIMATION = "death_animation"
    BATTLE_END = "battle_end"
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

    # マップ描画共通メソッド群
    def draw_map_background(self, map_scene):
        """マップ背景の描画"""
        from game import screen_height, screen_width

        # 画面に表示するタイルの範囲を計算
        start_col = int(map_scene.camera_x // map_scene.tile_size)
        end_col = min(
            int((map_scene.camera_x + screen_width) // map_scene.tile_size) + 1,
            map_scene.map_width,
        )
        start_row = int(map_scene.camera_y // map_scene.tile_size)
        end_row = min(
            int((map_scene.camera_y + screen_height) // map_scene.tile_size) + 1,
            map_scene.map_height,
        )

        # マップを描画（カメラ位置を考慮）
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if 0 <= row < map_scene.map_height and 0 <= col < map_scene.map_width:
                    x = col * map_scene.tile_size - map_scene.camera_x
                    y = row * map_scene.tile_size - map_scene.camera_y

                    if map_scene.map_data[row][col] == 1:
                        # 壁（茶色）
                        pyxel.rect(x, y, map_scene.tile_size, map_scene.tile_size, 4)
                    else:
                        # 床（薄い色）
                        pyxel.rect(x, y, map_scene.tile_size, map_scene.tile_size, 6)

    def draw_roads(self, map_scene):
        """道路の描画"""
        for road in self.context.game_state.roads:
            city1 = self.context.game_state.get_city_by_id(road.city1_id)
            city2 = self.context.game_state.get_city_by_id(road.city2_id)

            if city1 and city2:
                city1_screen_x = city1.x - map_scene.camera_x
                city1_screen_y = city1.y - map_scene.camera_y
                city2_screen_x = city2.x - map_scene.camera_x
                city2_screen_y = city2.y - map_scene.camera_y

                # 線分が画面と交差するかチェック
                if map_scene.line_intersects_screen(
                    city1_screen_x, city1_screen_y, city2_screen_x, city2_screen_y
                ):
                    pyxel.line(
                        city1_screen_x,
                        city1_screen_y,
                        city2_screen_x,
                        city2_screen_y,
                        9,
                    )  # オレンジ色の線

    def draw_cities(self, map_scene):
        """都市の描画"""
        from game import screen_height, screen_width

        for city_name, city in self.context.game_state.cities.items():
            city_screen_x = city.x - map_scene.camera_x
            city_screen_y = city.y - map_scene.camera_y

            # Cityが画面内にある場合のみ描画
            if (
                -city.size <= city_screen_x <= screen_width + city.size
                and -city.size <= city_screen_y <= screen_height + city.size
            ):
                half_size = city.size // 2
                # City本体（青色の円）
                pyxel.circb(city_screen_x, city_screen_y, half_size, 12)  # 青色の枠
                pyxel.circ(
                    city_screen_x, city_screen_y, half_size - 2, 1
                )  # 濃い青の内部

                # City名前を表示
                display_name = city.name
                text_x = city_screen_x - len(display_name) * 2
                text_y = city_screen_y + half_size + 2
                pyxel.text(text_x, text_y, display_name, 7)  # 白文字

    def draw_map_characters(self, map_scene):
        """マップ上のキャラクター描画"""
        # キャラクターの描画位置を計算（重なりを防ぐ）
        character_positions = map_scene.get_character_positions_by_city()

        # プレイヤーを描画
        self.draw_players(map_scene, character_positions)

        # 敵キャラクターを描画
        self.draw_enemies(map_scene, character_positions)

    def draw_players(self, map_scene, character_positions):
        """プレイヤーキャラクターの描画"""
        for i, player in enumerate(self.context.game_state.players):
            # キャラクターの描画位置を計算
            player_screen_x, player_screen_y = self.calculate_character_screen_position(
                player, map_scene, character_positions, "player"
            )

            # プレイヤーが画面内にある場合のみ描画
            if self.is_character_on_screen(player, player_screen_x, player_screen_y):
                # キャラクター描画
                self.draw_map_character(player, player_screen_x, player_screen_y)

                # ライフゲージを表示
                self.draw_life_gauge(player, player_screen_x, player_screen_y)

                # 選択されたプレイヤーに点滅する枠線を描画
                # プレイヤーターン中かつプレイヤーが移動していない場合のみ表示
                if (
                    player == map_scene.selected_player
                    and self.context.game_state.current_turn == "player"
                    and not player.is_moving
                ):
                    self.draw_character_selection_frame(
                        player, player_screen_x, player_screen_y, 11
                    )

    def draw_enemies(self, map_scene, character_positions):
        """敵キャラクターの描画"""
        for i, enemy in enumerate(self.context.game_state.enemies):
            # キャラクターの描画位置を計算
            enemy_screen_x, enemy_screen_y = self.calculate_character_screen_position(
                enemy, map_scene, character_positions, "enemy"
            )

            # 敵が画面内にある場合のみ描画
            if self.is_character_on_screen(enemy, enemy_screen_x, enemy_screen_y):
                # キャラクター描画
                self.draw_map_character(enemy, enemy_screen_x, enemy_screen_y)

                # ライフゲージを表示
                self.draw_life_gauge(enemy, enemy_screen_x, enemy_screen_y)

                # AI種別インジケーターを表示
                self.draw_ai_indicator(enemy, enemy_screen_x, enemy_screen_y)

                # AI思考中のインジケーター
                self.draw_ai_thinking_indicator(
                    enemy, enemy_screen_x, enemy_screen_y, map_scene
                )

                # 選択された敵に点滅する枠線を描画
                if (
                    enemy == map_scene.selected_enemy
                    and self.context.game_state.current_turn == "enemy"
                ):
                    self.draw_enemy_selection_frame(
                        enemy, enemy_screen_x, enemy_screen_y, map_scene
                    )

    def calculate_character_screen_position(
        self, character, map_scene, character_positions, char_type
    ):
        """キャラクターのスクリーン座標を計算"""
        if character.current_city_id and not character.is_moving:
            # 移動中でない場合のみ同じCity内での位置調整を行う
            current_city = self.context.game_state.get_city_by_id(
                character.current_city_id
            )
            if current_city and current_city in character_positions:
                city_characters = character_positions[current_city]
                char_index = next(
                    (
                        idx
                        for idx, (c_type, char) in enumerate(city_characters)
                        if c_type == char_type and char == character
                    ),
                    0,
                )

                # 複数キャラクターがいる場合は横に並べる
                offset_x = 0
                if len(city_characters) > 1:
                    total_width = len(city_characters) * character.width
                    start_x = -(total_width - character.width) // 2
                    offset_x = start_x + char_index * character.width

                screen_x = character.x + offset_x - map_scene.camera_x
            else:
                screen_x = character.x - map_scene.camera_x
        else:
            # 移動中または現在のCityがない場合はオフセットなし
            screen_x = character.x - map_scene.camera_x

        screen_y = character.y - map_scene.camera_y
        return screen_x, screen_y

    def is_character_on_screen(self, character, screen_x, screen_y):
        """キャラクターが画面内にあるかチェック"""
        from game import screen_height, screen_width

        return (
            -character.width <= screen_x <= screen_width + character.width
            and -character.height <= screen_y <= screen_height + character.height
        )

    def draw_map_character(self, character, screen_x, screen_y):
        """マップ用キャラクター描画"""
        half_width = character.width // 2
        half_height = character.height // 2

        # アニメーションフレームを計算（2つのフレームを交互に表示）
        anim_frame = (pyxel.frame_count // 10) % 2
        src_x = anim_frame * 16  # 0または16
        src_y = character.image_index * 16  # image_indexに基づいてY座標を計算

        # 向いている方向に応じて描画幅を調整
        draw_width = character.width if not character.facing_right else -character.width

        pyxel.blt(
            int(screen_x - half_width),
            int(screen_y - half_height),
            0,  # Image Bank 0
            src_x,
            src_y,
            draw_width,  # 幅（負の値で左右反転）
            character.height,
            2,  # 透明色
        )

    def draw_life_gauge(self, character, screen_x, screen_y):
        """ライフゲージの描画"""
        half_width = character.width // 2
        half_height = character.height // 2
        life_bar_width = character.width
        life_bar_height = 3
        life_bar_x = int(screen_x - half_width)
        life_bar_y = int(screen_y - half_height - 8)

        # ライフゲージの背景（赤色）
        pyxel.rect(life_bar_x, life_bar_y, life_bar_width, life_bar_height, 8)

        # ライフゲージの現在値（緑色）
        current_life_width = int((character.life / character.max_life) * life_bar_width)
        if current_life_width > 0:
            pyxel.rect(life_bar_x, life_bar_y, current_life_width, life_bar_height, 11)

    def draw_character_selection_frame(self, character, screen_x, screen_y, color):
        """キャラクター選択枠の描画"""
        half_width = character.width // 2
        half_height = character.height // 2

        # 点滅効果（30フレームで1回点滅）
        if (pyxel.frame_count // 10) % 3 != 0:
            # 枠線を描画
            frame_x = int(screen_x - half_width - 1)
            frame_y = int(screen_y - half_height - 1)
            frame_w = character.width + 2
            frame_h = character.height + 2

            # 上下の線
            pyxel.rect(frame_x, frame_y, frame_w, 1, color)
            pyxel.rect(frame_x, frame_y + frame_h - 1, frame_w, 1, color)
            # 左右の線
            pyxel.rect(frame_x, frame_y, 1, frame_h, color)
            pyxel.rect(frame_x + frame_w - 1, frame_y, 1, frame_h, color)

    def draw_ai_indicator(self, enemy, screen_x, screen_y):
        """AI種別インジケーターの描画"""
        half_height = enemy.height // 2
        indicator_x = int(screen_x)
        indicator_y = int(screen_y - half_height - 6)

        if enemy.ai_type == "aggressive":
            pyxel.circ(indicator_x, indicator_y, 2, 8)  # 赤色
        elif enemy.ai_type == "patrol":
            pyxel.circ(indicator_x, indicator_y, 2, 11)  # ライトブルー
        elif enemy.ai_type == "defensive":
            pyxel.circ(indicator_x, indicator_y, 2, 3)  # 緑色
        else:  # random
            pyxel.circ(indicator_x, indicator_y, 2, 14)  # ピンク

    def draw_ai_thinking_indicator(self, enemy, screen_x, screen_y, map_scene):
        """AI思考中インジケーターの描画"""
        half_height = enemy.height // 2
        current_ai_enemy = None
        if (
            self.context.game_state.current_ai_enemy_index is not None
            and 0
            <= self.context.game_state.current_ai_enemy_index
            < len(self.context.game_state.enemies)
        ):
            current_ai_enemy = self.context.game_state.enemies[
                self.context.game_state.current_ai_enemy_index
            ]

        if (
            self.context.game_state.current_turn == "enemy"
            and self.context.game_state.ai_timer > 0
            and enemy == current_ai_enemy
        ):
            # 点滅する思考インジケーター
            if (pyxel.frame_count // 5) % 2 == 0:
                pyxel.circ(
                    int(screen_x),
                    int(screen_y - half_height - 12),
                    3,
                    7,
                )  # 白色の思考バブル

    def draw_enemy_selection_frame(self, enemy, screen_x, screen_y, map_scene):
        """敵選択枠の描画"""
        half_width = enemy.width // 2
        half_height = enemy.height // 2

        # EnemySelectionState中は特別な点滅効果
        current_state_type = map_scene.state_context.get_current_state_type()

        if current_state_type == MapStateType.ENEMY_SELECTION:
            # EnemySelectionState中の点滅
            current_state = map_scene.state_context.current_state
            if hasattr(current_state, "blink_timer") and hasattr(
                current_state, "blink_duration"
            ):
                blink_phase = current_state.blink_timer % current_state.blink_duration
                if blink_phase < current_state.blink_duration // 2:
                    frame_color = 8  # 赤色

                    # 枠線を描画
                    frame_x = int(screen_x - half_width - 2)
                    frame_y = int(screen_y - half_height - 2)
                    frame_w = enemy.width + 4
                    frame_h = enemy.height + 4

                    # 太い枠線で強調
                    pyxel.rect(frame_x, frame_y, frame_w, 2, frame_color)  # 上
                    pyxel.rect(
                        frame_x, frame_y + frame_h - 2, frame_w, 2, frame_color
                    )  # 下
                    pyxel.rect(frame_x, frame_y, 2, frame_h, frame_color)  # 左
                    pyxel.rect(
                        frame_x + frame_w - 2, frame_y, 2, frame_h, frame_color
                    )  # 右
        else:
            # 通常の点滅効果
            self.draw_character_selection_frame(enemy, screen_x, screen_y, 8)

    def draw_phase(self, map_scene):
        """状態固有の描画（各状態でオーバーライド）"""
        # デフォルトでは何も描画しない
        pass


class StateContext:
    """状態管理コンテキスト"""

    def __init__(self):
        self.current_state = None
        self.previous_state = None
        self.state_history = []  # デバッグ用状態履歴
        self.game_state = None  # GameStateへの参照を追加

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
                displayed_life = self.context.get_displayed_life(
                    player, initial_life, "player"
                )
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

    def draw_character(
        self, character, x, y, facing_right, initial_life, character_type
    ):
        """キャラクターを指定位置に描画（各状態でオーバーライド可能）"""
        half_width = character.width // 2
        half_height = character.height // 2

        # アニメーションフレームを計算（戦闘中はゆっくりとしたアニメーション）
        anim_frame = (pyxel.frame_count // 20) % 2
        src_x = anim_frame * 16
        src_y = character.image_index * 16

        # 向きに応じて描画幅を調整（map.pyと同じ論理に修正）
        draw_width = character.width if not facing_right else -character.width

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

    @abstractmethod
    def draw_phase(self):
        """状態固有の描画（各状態でオーバーライド）"""
        pass
