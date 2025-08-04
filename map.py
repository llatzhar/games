import random

import pyxel

from coordinate_utils import create_default_coordinate_transformer

# game.pyから定数をインポート
from game import Scene, screen_height, screen_width
from game_state import City, GameState
from geometry_utils import line_intersects_line
from hover_info import HoverInfo
from map_state_machine import StateContext
from map_states import PlayerTurnState


class MapScene(Scene):
    def __init__(self):
        super().__init__()
        self.selected_player = None  # 選択中のプレイヤー
        self.debug_page = 0  # デバッグ情報のページ番号 (0=非表示, 1〜3=ページ)
        self.max_debug_page = 3  # デバッグページの最大数

        # ゲーム状態を初期化
        self.game_state = GameState()

        # セーブファイルがあれば読み込み、なければデフォルト状態で初期化
        if not self.game_state.load_from_file():
            self.game_state.initialize_default_state()
            self.game_state.save_to_file()  # 初回作成時はセーブ

        self.selected_enemy = None  # 選択中の敵（エネミーターン用）

        # 戦闘処理用（後方互換性のため残す）
        self.pending_battle_results = []  # 処理待ちの戦闘結果
        self.current_battle_index = 0  # 現在処理中の戦闘インデックス
        self.is_processing_battles = False  # 戦闘処理中フラグ

        # カメラ位置（ビューの左上座標）- MapSceneが保持
        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 4  # カメラの移動速度

        # カメラ追従システム
        self.camera_follow_target = None  # 追従対象のキャラクター
        self.camera_target_x = 0  # カメラの目標X座標
        self.camera_target_y = 0  # カメラの目標Y座標
        self.camera_follow_speed = 6  # 追従時のカメラ移動速度
        self.camera_offset_x = screen_width // 2  # カメラの中央オフセット
        self.camera_offset_y = screen_height // 2  # カメラの中央オフセット

        # プレイヤーの位置に基づいてカメラの初期位置を設定
        if self.game_state.players:
            first_player = self.game_state.players[0]
            self.camera_x = first_player.x - self.camera_offset_x
            self.camera_y = first_player.y - self.camera_offset_y

        # マウスカーソルを表示
        pyxel.mouse(True)

        # 座標変換器を初期化
        self.coord_transformer = create_default_coordinate_transformer()

        # 座標変換器からマップ設定を取得
        self.map_width = self.coord_transformer.map_width
        self.map_height = self.coord_transformer.map_height
        self.tile_size = self.coord_transformer.tile_size
        self.tile_offset_x = self.coord_transformer.tile_offset_x
        self.tile_offset_y = self.coord_transformer.tile_offset_y

        # 30x30のマップデータを生成（中央座標系対応）
        self.map_data = self.generate_centered_map()

        # マップ全体のピクセルサイズ
        self.map_pixel_width = self.map_width * self.tile_size
        self.map_pixel_height = self.map_height * self.tile_size

        # ホバー情報表示
        self.hover_info = HoverInfo()

        # 状態マシン初期化
        self.state_context = StateContext()
        self.state_context.game_state = self.game_state  # GameStateの参照を設定
        self.state_context.change_state(PlayerTurnState(self))

        # シーン遷移用
        self.next_scene = None
        self.battle_sequence_state = None  # 戦闘シーケンス状態の保存

    def generate_centered_map(self):
        """17x17の中央座標系マップを生成（タイル座標-8〜8）"""
        map_data = []
        for row in range(17):  # マップ配列インデックス0〜16
            map_row = []
            for col in range(17):  # マップ配列インデックス0〜16
                # マップ配列インデックスをタイル座標に変換
                tile_x = col - 8  # -8 〜 8
                tile_y = row - 8  # -8 〜 8

                # 外周は壁（タイル座標-8, 8の境界）
                if tile_x == -8 or tile_x == 8 or tile_y == -8 or tile_y == 8:
                    map_row.append(1)
                # 内部にランダムに壁を配置（中央座標系のパターン）
                elif tile_y % 4 == 0 and tile_x % 4 == 0:
                    map_row.append(1)
                # 特定のパターンで壁を配置
                elif tile_y % 6 == 2 and tile_x % 6 == 2:
                    map_row.append(1)
                elif tile_y % 8 == 3 and tile_x % 3 == 1:
                    map_row.append(1)
                else:
                    map_row.append(0)
            map_data.append(map_row)
        return map_data

    def tile_to_pixel(self, tile_x: int, tile_y: int) -> tuple[float, float]:
        """タイル座標をピクセル座標に変換（中央座標系対応）"""
        return self.coord_transformer.tile_to_pixel(tile_x, tile_y)

    def pixel_to_tile(self, pixel_x: float, pixel_y: float) -> tuple[int, int]:
        """ピクセル座標をタイル座標に変換（中央座標系対応）"""
        return self.coord_transformer.pixel_to_tile(pixel_x, pixel_y)

    def tile_to_map_index(self, tile_x: int, tile_y: int) -> tuple[int, int]:
        """タイル座標をマップ配列インデックスに変換"""
        return self.coord_transformer.tile_to_map_index(tile_x, tile_y)

    def map_index_to_tile(self, map_col: int, map_row: int) -> tuple[int, int]:
        """マップ配列インデックスをタイル座標に変換"""
        return self.coord_transformer.map_index_to_tile(map_col, map_row)

    def is_valid_tile(self, tile_x: int, tile_y: int) -> bool:
        """タイル座標が有効範囲内かチェック"""
        return self.coord_transformer.is_valid_tile_coordinate(tile_x, tile_y)

    def get_tile_type(self, tile_x: int, tile_y: int) -> int:
        """タイル座標でマップデータを取得"""
        if not self.is_valid_tile(tile_x, tile_y):
            return 1  # 範囲外は壁扱い

        map_col, map_row = self.tile_to_map_index(tile_x, tile_y)
        return self.map_data[map_row][map_col]

    def set_camera_follow_target(self, target):
        """カメラ追従対象を設定"""
        self.camera_follow_target = target
        if target:
            # 目標位置を即座に設定
            self.camera_target_x = target.x - self.camera_offset_x
            self.camera_target_y = target.y - self.camera_offset_y

    def update_camera_follow(self):
        """カメラ追従の更新処理"""
        if self.camera_follow_target:
            # 追従対象の現在位置を目標位置として設定
            target_camera_x = self.camera_follow_target.x - self.camera_offset_x
            target_camera_y = self.camera_follow_target.y - self.camera_offset_y

            # マップ範囲内に制限
            target_camera_x = max(
                0, min(target_camera_x, self.map_pixel_width - screen_width)
            )
            target_camera_y = max(
                0, min(target_camera_y, self.map_pixel_height - screen_height)
            )

            # スムーズにカメラを移動
            dx = target_camera_x - self.camera_x
            dy = target_camera_y - self.camera_y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance > 1:  # 目標位置に十分近い場合は移動停止
                # 追従速度で移動
                move_distance = min(self.camera_follow_speed, distance)
                self.camera_x += (dx / distance) * move_distance
                self.camera_y += (dy / distance) * move_distance
            else:
                # 目標位置に到達
                self.camera_x = target_camera_x
                self.camera_y = target_camera_y

    def clear_camera_follow(self):
        """カメラ追従をクリア"""
        self.camera_follow_target = None

    def get_connected_cities(self, city):
        """指定したCityに接続されているCityのリストを取得"""
        if isinstance(city, City):
            city_id = city.id
        else:
            city_id = city

        connected_ids = self.game_state.get_connected_city_ids(city_id)
        return [
            self.game_state.get_city_by_id(city_id)
            for city_id in connected_ids
            if self.game_state.get_city_by_id(city_id)
        ]

    def get_distance_to_nearest_player(self, enemy_city):
        """指定したCityから最も近いプレイヤーまでの距離を計算"""
        min_distance = float("inf")
        nearest_player = None

        for player in self.game_state.players:
            if player.current_city_id:
                player_city = self.game_state.get_city_by_id(player.current_city_id)
                if player_city:
                    dx = player_city.x - enemy_city.x
                    dy = player_city.y - enemy_city.y
                    distance = (dx * dx + dy * dy) ** 0.5
                    if distance < min_distance:
                        min_distance = distance
                        nearest_player = player

        return min_distance, nearest_player

    def find_path_to_target(self, start_city, target_city):
        """簡単なパス検索（BFS）で目標Cityへの最短経路を見つける"""
        if start_city == target_city:
            return []

        # 都市IDで処理
        start_id = start_city.id if isinstance(start_city, City) else start_city
        target_id = target_city.id if isinstance(target_city, City) else target_city

        if start_id == target_id:
            return []

        # BFS for pathfinding
        queue = [(start_id, [])]
        visited = {start_id}

        while queue:
            current_city_id, path = queue.pop(0)

            for connected_city_id in self.game_state.get_connected_city_ids(
                current_city_id
            ):
                if connected_city_id == target_id:
                    result_cities = []
                    for city_id in path + [connected_city_id]:
                        city = self.game_state.get_city_by_id(city_id)
                        if city:
                            result_cities.append(city)
                    return result_cities

                if connected_city_id not in visited:
                    visited.add(connected_city_id)
                    queue.append((connected_city_id, path + [connected_city_id]))

        return []  # No path found

    def decide_enemy_action(self, enemy):
        """敵のAIに基づいて行動を決定"""
        if not enemy.current_city_id:
            return None

        current_city = self.game_state.get_city_by_id(enemy.current_city_id)
        if not current_city:
            return None

        connected_cities = self.get_connected_cities(current_city)
        if not connected_cities:
            return None

        if enemy.ai_type == "random":
            # ランダムに接続されたCityから選択
            return random.choice(connected_cities)

        elif enemy.ai_type == "aggressive":
            # プレイヤーに近づこうとする行動
            min_distance, nearest_player = self.get_distance_to_nearest_player(
                current_city
            )

            if nearest_player and nearest_player.current_city_id:
                nearest_player_city = self.game_state.get_city_by_id(
                    nearest_player.current_city_id
                )
                if nearest_player_city:
                    # プレイヤーに向かうパスを検索
                    path = self.find_path_to_target(current_city, nearest_player_city)
                    if path:
                        # パスの最初のステップに移動
                        return path[0]

            # プレイヤーが見つからない場合はランダム移動
            return random.choice(connected_cities)

        elif enemy.ai_type == "defensive":
            # プレイヤーから遠ざかろうとする行動
            min_distance, nearest_player = self.get_distance_to_nearest_player(
                current_city
            )

            if nearest_player and nearest_player.current_city_id:
                nearest_player_city = self.game_state.get_city_by_id(
                    nearest_player.current_city_id
                )
                if nearest_player_city:
                    best_city = None
                    max_distance = min_distance

                    # 接続されたCityの中で最もプレイヤーから遠いCityを選択
                    for city in connected_cities:
                        dx = nearest_player_city.x - city.x
                        dy = nearest_player_city.y - city.y
                        distance = (dx * dx + dy * dy) ** 0.5

                        if distance > max_distance:
                            max_distance = distance
                            best_city = city

                    if best_city:
                        return best_city

            # 遠ざかる場所がない場合はランダム移動
            return random.choice(connected_cities)

        elif enemy.ai_type == "patrol":
            # パトロールルートに沿って移動
            if enemy.patrol_city_ids and len(enemy.patrol_city_ids) > 1:
                # 次のパトロール地点を取得
                next_index = (enemy.patrol_index + 1) % len(enemy.patrol_city_ids)
                target_city_id = enemy.patrol_city_ids[next_index]
                target_city = self.game_state.get_city_by_id(target_city_id)

                if target_city:
                    # 現在位置から次のパトロール地点への経路を検索
                    path = self.find_path_to_target(current_city, target_city)
                    if path:
                        # パスの最初のステップに移動
                        return path[0]
                    else:
                        # 直接接続されているかチェック
                        if target_city in connected_cities:
                            enemy.patrol_index = next_index
                            return target_city

            # パトロールルートが設定されていない場合はランダム移動
            return random.choice(connected_cities)

        # デフォルトはランダム移動
        return random.choice(connected_cities)

    def get_character_positions_by_city(self):
        """各Cityにいるキャラクターを収集して辞書で返す"""
        character_positions = {}
        for city_id, city in self.game_state.cities.items():
            character_positions[city] = []
            for player in self.game_state.players:
                if player.current_city_id == city_id:
                    character_positions[city].append(("player", player))
            for enemy in self.game_state.enemies:
                if enemy.current_city_id == city_id:
                    character_positions[city].append(("enemy", enemy))
        return character_positions

    def get_player_at_position(self, screen_x, screen_y):
        """指定したスクリーン座標にいるプレイヤーを取得"""
        # スクリーン座標をワールド座標に変換
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y

        # 各Cityにいるキャラクターを収集
        character_positions = self.get_character_positions_by_city()

        for player in self.game_state.players:
            # キャラクターの描画位置を計算（重なり防止と同じロジック）
            if player.current_city_id and not player.is_moving:
                # 移動中でない場合のみオフセットを適用
                current_city = self.game_state.get_city_by_id(player.current_city_id)
                if current_city and current_city in character_positions:
                    city_characters = character_positions[current_city]
                    char_index = next(
                        (
                            idx
                            for idx, (char_type, char) in enumerate(city_characters)
                            if char_type == "player" and char == player
                        ),
                        0,
                    )

                    offset_x = 0
                    if len(city_characters) > 1:
                        total_width = len(city_characters) * player.width
                        start_x = -(total_width - player.width) // 2
                        offset_x = start_x + char_index * player.width

                    adjusted_x = player.x + offset_x
                else:
                    adjusted_x = player.x
            else:
                # 移動中または現在のCityがない場合はオフセットなし
                adjusted_x = player.x

            # プレイヤーの範囲内かチェック
            half_width = player.width // 2
            half_height = player.height // 2
            if (
                adjusted_x - half_width <= world_x <= adjusted_x + half_width
                and player.y - half_height <= world_y <= player.y + half_height
            ):
                return player
        return None

    def get_city_at_position(self, screen_x, screen_y):
        """指定したスクリーン座標にあるCityを取得"""
        # スクリーン座標をワールド座標に変換
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y

        for city_name, city in self.game_state.cities.items():
            # Cityの範囲内かチェック
            half_size = city.size // 2
            if (
                city.x - half_size <= world_x <= city.x + half_size
                and city.y - half_size <= world_y <= city.y + half_size
            ):
                return city
        return None

    def get_player_current_city(self, player):
        """プレイヤーが現在いるCityを取得"""
        if player.current_city_id:
            return self.game_state.get_city_by_id(player.current_city_id)
        return None

    def is_cities_connected(self, city1, city2):
        """2つのCity間がRoadで接続されているかチェック"""
        # Cityオブジェクトから内部IDを取得
        if isinstance(city1, City):
            city1_id = city1.id
        else:
            city1_id = city1

        if isinstance(city2, City):
            city2_id = city2.id
        else:
            city2_id = city2

        return self.game_state.are_cities_connected(city1_id, city2_id)

    def line_intersects_screen(self, x1, y1, x2, y2):
        """線分が画面と交差するかチェック"""
        # 画面の境界
        screen_left = 0
        screen_right = screen_width
        screen_top = 0
        screen_bottom = screen_height

        # 両端点が画面内にある場合
        if (
            screen_left <= x1 <= screen_right and screen_top <= y1 <= screen_bottom
        ) or (screen_left <= x2 <= screen_right and screen_top <= y2 <= screen_bottom):
            return True

        # 線分のバウンディングボックスが画面と交差するかチェック
        line_left = min(x1, x2)
        line_right = max(x1, x2)
        line_top = min(y1, y2)
        line_bottom = max(y1, y2)

        # バウンディングボックスが画面と重複しない場合は交差しない
        if (
            line_right < screen_left
            or line_left > screen_right
            or line_bottom < screen_top
            or line_top > screen_bottom
        ):
            return False

        # より詳細な線分交差判定（線分が画面境界と交差するかチェック）
        return (
            line_intersects_line(
                x1, y1, x2, y2, screen_left, screen_top, screen_right, screen_top
            )  # 上辺
            or line_intersects_line(
                x1, y1, x2, y2, screen_right, screen_top, screen_right, screen_bottom
            )  # 右辺
            or line_intersects_line(
                x1, y1, x2, y2, screen_right, screen_bottom, screen_left, screen_bottom
            )  # 下辺
            or line_intersects_line(
                x1, y1, x2, y2, screen_left, screen_bottom, screen_left, screen_top
            )
        )  # 左辺

    def start_battle_sequence(self, battle_locations):
        """戦闘シーケンスを開始"""
        if not battle_locations:
            return

        self.pending_battle_results = battle_locations
        self.current_battle_index = 0
        self.is_processing_battles = True

        # 最初の戦闘がある都市にカメラを移動
        self.process_next_battle()

    def process_next_battle(self):
        """次の戦闘を処理"""
        if self.current_battle_index >= len(self.pending_battle_results):
            # 全ての戦闘処理が完了
            self.finish_battle_sequence()
            return

        current_battle = self.pending_battle_results[self.current_battle_index]
        city_id = current_battle["city_id"]
        city = self.game_state.get_city_by_id(city_id)

        if city:
            # 戦闘があった都市にカメラを移動
            self.move_camera_to_city(city)

            # 少し待ってから戦闘サブシーンを開始
            self.battle_camera_timer = 60  # 2秒待機

    def move_camera_to_city(self, city):
        """カメラを指定した都市に移動"""
        target_camera_x = city.x - self.camera_offset_x
        target_camera_y = city.y - self.camera_offset_y

        # マップ範囲内に制限
        target_camera_x = max(
            0, min(target_camera_x, self.map_pixel_width - screen_width)
        )
        target_camera_y = max(
            0, min(target_camera_y, self.map_pixel_height - screen_height)
        )

        # カメラ位置を即座に設定（アニメーションなしで即移動）
        self.camera_x = target_camera_x
        self.camera_y = target_camera_y

        # カメラ追従をクリア
        self.clear_camera_follow()

    # 古い戦闘処理メソッドは削除済み - 新しいBattleSceneを使用

    def on_sub_scene_finished(self, finished_sub_scene):
        """サブシーン終了時の処理"""
        print("SubScene finished:", finished_sub_scene)
        # 古い戦闘処理は無効化 - 新しいBattleSceneを使用
        pass

    def can_move_this_turn(self):
        """このターンで移動可能かチェック"""
        return self.game_state.can_move_this_turn()

    def get_enemy_at_position(self, screen_x, screen_y):
        """指定したスクリーン座標にいる敵を取得"""
        # スクリーン座標をワールド座標に変換
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y

        # 各Cityにいるキャラクターを収集
        character_positions = self.get_character_positions_by_city()

        for enemy in self.game_state.enemies:
            # キャラクターの描画位置を計算（重なり防止と同じロジック）
            if enemy.current_city_id and not enemy.is_moving:
                # 移動中でない場合のみオフセットを適用
                current_city = self.game_state.get_city_by_id(enemy.current_city_id)
                if current_city and current_city in character_positions:
                    city_characters = character_positions[current_city]
                    char_index = next(
                        (
                            idx
                            for idx, (char_type, char) in enumerate(city_characters)
                            if char_type == "enemy" and char == enemy
                        ),
                        0,
                    )

                    offset_x = 0
                    if len(city_characters) > 1:
                        total_width = len(city_characters) * enemy.width
                        start_x = -(total_width - enemy.width) // 2
                        offset_x = start_x + char_index * enemy.width

                    adjusted_x = enemy.x + offset_x
                else:
                    adjusted_x = enemy.x
            else:
                # 移動中または現在のCityがない場合はオフセットなし
                adjusted_x = enemy.x

            # 敵の範囲内かチェック
            half_width = enemy.width // 2
            half_height = enemy.height // 2
            if (
                adjusted_x - half_width <= world_x <= adjusted_x + half_width
                and enemy.y - half_height <= world_y <= enemy.y + half_height
            ):
                return enemy
        return None

    def update(self):
        # サブシーンの処理を先に実行
        if super().update():
            return self

        # 共通入力処理（全状態で有効）
        # Qキーでタイトルシーンに戻る
        if pyxel.btnp(pyxel.KEY_Q):
            from game import TitleScene

            return TitleScene()

        # Vキーでデバッグ情報のページ切り替え
        if pyxel.btnp(pyxel.KEY_V):
            self.debug_page = (self.debug_page + 1) % (self.max_debug_page + 1)

        # 状態マシンの更新
        result = self.state_context.update()
        if result != self:
            return result

        # 状態固有の入力処理
        self.state_context.handle_input()

        # シーン遷移チェック
        if self.next_scene:
            next_scene = self.next_scene
            self.next_scene = None  # リセット
            return next_scene

        # 戦闘終了後の復帰処理
        if self.battle_sequence_state:
            battle_state = self.battle_sequence_state
            self.battle_sequence_state = None  # リセット

            # 戦闘完了後の処理を継続
            battle_state.on_battle_finished()
            return self

        # カメラ追従の更新処理
        self.update_camera_follow()

        # カメラの手動移動（WASDキー）- 敵ターン中で追従対象がある場合は無効
        if not (self.game_state.current_turn == "enemy" and self.camera_follow_target):
            if pyxel.btn(pyxel.KEY_W):
                self.camera_y -= self.camera_speed
                self.clear_camera_follow()  # 手動操作時は追従をクリア
            if pyxel.btn(pyxel.KEY_S):
                self.camera_y += self.camera_speed
                self.clear_camera_follow()  # 手動操作時は追従をクリア
            if pyxel.btn(pyxel.KEY_A):
                self.camera_x -= self.camera_speed
                self.clear_camera_follow()  # 手動操作時は追従をクリア
            if pyxel.btn(pyxel.KEY_D):
                self.camera_x += self.camera_speed
                self.clear_camera_follow()  # 手動操作時は追従をクリア

        # カメラ位置をマップ範囲内に制限
        self.camera_x = max(0, min(self.camera_x, self.map_pixel_width - screen_width))
        self.camera_y = max(
            0, min(self.camera_y, self.map_pixel_height - screen_height)
        )

        return self

    def change_state(self, new_state):
        """状態を変更（StateContextへの委譲）"""
        self.state_context.change_state(new_state)

    def transition_to_scene(self, new_scene):
        """シーン遷移（状態マシンから呼び出される）"""
        return new_scene

    def draw(self):
        # サブシーンがある場合はサブシーンを描画
        if super().draw():
            return

        # メインの描画
        pyxel.cls(3)  # 背景色

        # 状態マシンに描画を委譲
        if self.state_context.current_state:
            # 共通の背景描画
            self.state_context.current_state.draw_map_background(self)
            self.state_context.current_state.draw_roads(self)
            self.state_context.current_state.draw_cities(self)
            self.state_context.current_state.draw_map_characters(self)

            # 状態固有の描画
            self.state_context.current_state.draw_phase(self)

        # UI表示（全状態共通）
        self.draw_ui()

    def draw_ui(self):
        """UI表示（ホバー情報、ゲーム終了オーバーレイ、デバッグ情報）"""
        # ホバー情報の表示（最優先で表示）
        mouse_x = pyxel.mouse_x
        mouse_y = pyxel.mouse_y
        hovered_character = self.get_player_at_position(mouse_x, mouse_y)
        if not hovered_character:
            hovered_character = self.get_enemy_at_position(mouse_x, mouse_y)
        hovered_city = self.get_city_at_position(mouse_x, mouse_y)

        self.hover_info.draw_hover_info(
            mouse_x, mouse_y, hovered_character, hovered_city, self.game_state
        )

        # デバッグ情報の表示（ページ切り替え対応）
        if self.debug_page > 0:
            self.draw_debug_page(self.debug_page)
        else:
            # デバッグ情報非表示時は最小限の情報のみ
            pyxel.text(5, 5, "Press V for debug info", 8)

    def draw_debug_page(self, page):
        """デバッグ情報のページを描画"""
        # ページ番号表示
        page_text = f"Debug Page {page}/{self.max_debug_page} (V to switch)"
        pyxel.text(5, 5, page_text, 7)

        if page == 1:
            # ページ1: 基本操作とターン情報
            pyxel.text(5, 15, "Map Scene (30x30) - Press Q to Title", 7)
            if self.game_state.current_turn == "enemy" and self.camera_follow_target:
                pyxel.text(5, 25, "Camera following enemy - Manual control disabled", 6)
            else:
                pyxel.text(5, 25, "WASD: Move Camera, ESC: Deselect", 7)
            pyxel.text(5, 35, "Click: Select character, Click connected City", 7)

            # ターン情報を表示
            turn_counter = self.game_state.turn_counter
            turn_name = self.game_state.current_turn.upper()
            turn_text = f"Turn {turn_counter}: {turn_name} TURN"
            turn_color = 11 if self.game_state.current_turn == "player" else 8
            pyxel.text(5, 45, turn_text, turn_color)

            can_move = "YES" if self.can_move_this_turn() else "NO"
            move_text = f"Can move this turn: {can_move}"
            pyxel.text(5, 55, move_text, 10)

            # 状態マシン情報を表示
            self.state_context.draw_debug_info(5, 65)

            # 選択中のキャラクター情報を表示
            if self.game_state.current_turn == "player" and self.selected_player:
                current_city_id = (
                    self.selected_player.current_city_id
                    if self.selected_player.current_city_id
                    else None
                )
                # 都市の表示名を取得
                if current_city_id is not None:
                    display_name = self.game_state.get_city_display_name(
                        current_city_id
                    )
                else:
                    display_name = "None"
                selected_text = f"Selected Player at {display_name}:"
                pyxel.text(5, 65, selected_text, 11)
                pos_text = (
                    f"  Position: ({int(self.selected_player.x)}, "
                    f"{int(self.selected_player.y)})"
                )
                pyxel.text(5, 75, pos_text, 11)
                # プレイヤーの戦闘ステータスを表示
                player_life = self.selected_player.life
                player_max_life = self.selected_player.max_life
                player_attack = self.selected_player.attack
                status_text = (
                    f"  Life: {player_life}/{player_max_life}, "
                    f"Attack: {player_attack}"
                )
                pyxel.text(5, 85, status_text, 11)
            elif self.game_state.current_turn == "enemy" and self.selected_enemy:
                current_city_id = (
                    self.selected_enemy.current_city_id
                    if self.selected_enemy.current_city_id
                    else None
                )
                # 都市の表示名を取得
                if current_city_id is not None:
                    display_name = self.game_state.get_city_display_name(
                        current_city_id
                    )
                else:
                    display_name = "None"
                selected_text = f"Selected Enemy at {display_name}:"
                pyxel.text(5, 65, selected_text, 8)
                pos_text = (
                    f"  Position: ({int(self.selected_enemy.x)}, "
                    f"{int(self.selected_enemy.y)})"
                )
                pyxel.text(5, 75, pos_text, 8)
                # 敵の戦闘ステータスを表示
                enemy_life = self.selected_enemy.life
                enemy_max_life = self.selected_enemy.max_life
                enemy_attack = self.selected_enemy.attack
                status_text = (
                    f"  Life: {enemy_life}/{enemy_max_life}, "
                    f"Attack: {enemy_attack}"
                )
                pyxel.text(5, 85, status_text, 8)
            else:
                pyxel.text(5, 65, "No character selected", 8)

        elif page == 2:
            # ページ2: カメラとマップ情報
            pyxel.text(5, 15, "Camera & Map Information", 14)

            # カメラ位置を表示
            camera_text = f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})"
            pyxel.text(5, 25, camera_text, 10)

            # カメラ追従情報を表示
            if self.camera_follow_target:
                if hasattr(self.camera_follow_target, 'ai_type'):
                    target_type = self.camera_follow_target.ai_type
                else:
                    target_type = 'Player'
                follow_info = f"Camera following: {target_type}"
                pyxel.text(5, 35, follow_info, 13)
            else:
                pyxel.text(5, 35, "Camera: Manual control", 6)

            # Cities情報を表示
            pyxel.text(5, 50, "Cities:", 14)
            y_pos = 60
            for city_name, city in self.game_state.cities.items():
                if y_pos > screen_height - 10:  # 画面からはみ出さないように制限
                    break
                # 表示名を使用
                display_name = city.name
                city_info = f"{display_name}: ({int(city.x)}, {int(city.y)})"
                pyxel.text(5, y_pos, city_info, 12)
                y_pos += 10

        elif page == 3:
            # ページ3: キャラクター情報とAI情報
            pyxel.text(5, 15, "Characters & AI Information", 14)

            # プレイヤーの情報を表示
            pyxel.text(5, 25, "Players:", 14)
            y_pos = 35
            for i, player in enumerate(self.game_state.players):
                player_city_id = (
                    player.current_city_id if player.current_city_id else None
                )
                # 都市の表示名を取得
                if player_city_id is not None:
                    display_name = self.game_state.get_city_display_name(
                        player_city_id
                    )
                else:
                    display_name = "None"
                player_info = (
                    f"Player {i+1} at {display_name}: "
                    f"Life {player.life}/{player.max_life}"
                )
                pyxel.text(5, y_pos, player_info, 11)
                y_pos += 10

            # 敵の情報を表示
            y_pos += 5
            pyxel.text(5, y_pos, "Enemies:", 14)
            y_pos += 10
            for i, enemy in enumerate(self.game_state.enemies):
                enemy_city_id = enemy.current_city_id if enemy.current_city_id else None
                # 都市の表示名を取得
                if enemy_city_id is not None:
                    display_name = self.game_state.get_city_display_name(
                        enemy_city_id
                    )
                else:
                    display_name = "None"
                enemy_info = (
                    f"Enemy {i+1} ({enemy.ai_type}) at {display_name}:"
                )
                pyxel.text(5, y_pos, enemy_info, 8)
                y_pos += 10
                life_info = f"  Life {enemy.life}/{enemy.max_life}"
                pyxel.text(5, y_pos, life_info, 8)
                y_pos += 10

            # AI凡例を表示（画面の下部に）
            legend_y = screen_height - 35
            pyxel.text(5, legend_y, "AI Legend:", 14)
            pyxel.circ(15, legend_y + 8, 2, 8)  # 赤色
            pyxel.text(20, legend_y + 6, "Aggressive", 7)
            pyxel.circ(80, legend_y + 8, 2, 11)  # ライトブルー
            pyxel.text(85, legend_y + 6, "Patrol", 7)
            pyxel.circ(15, legend_y + 16, 2, 3)  # 緑色
            pyxel.text(20, legend_y + 14, "Defensive", 7)
            pyxel.circ(80, legend_y + 16, 2, 14)  # ピンク
            pyxel.text(85, legend_y + 14, "Random", 7)

            # 戦闘処理状態を表示
            if self.is_processing_battles:
                current_battle = self.current_battle_index + 1
                total_battles = len(self.pending_battle_results)
                battle_info = f"Processing battles: {current_battle}/{total_battles}"
                battle_y = legend_y - 20
                pyxel.text(5, battle_y, battle_info, 13)

            # 現在のマウス座標を表示
            # スクリーン座標からワールド座標に変換
            world_x = pyxel.mouse_x + self.camera_x
            world_y = pyxel.mouse_y + self.camera_y
            # ワールド座標からタイル座標に変換
            tile_x, tile_y = self.pixel_to_tile(world_x, world_y)

            mouse_text = (
                f"Mouse: ({pyxel.mouse_x}, {pyxel.mouse_y}) "
                f"Tile: ({tile_x}, {tile_y})"
            )
            mouse_y = (
                legend_y - 30
                if self.is_processing_battles
                else legend_y - 20
            )
            pyxel.text(5, mouse_y, mouse_text, 10)
