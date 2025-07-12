import pyxel
import math
import random

# game.pyから定数をインポート
from game import screen_width, screen_height, char_width, char_height, Scene, SubScene
from game_state import GameState, City, Road, Player, Enemy
from cutin import CutinSubScene
from battle import BattleSubScene
from hover_info import HoverInfo

class MapScene(Scene):
    def __init__(self):
        super().__init__()
        self.click_x = -1  # クリック位置のX座標
        self.click_y = -1  # クリック位置のY座標
        self.click_timer = 0  # クリック座標表示時間
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
        
        # 戦闘処理用
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
        
        # マウスカーソルを表示
        pyxel.mouse(True)
        
        # 30x30のマップデータを生成
        self.map_width = 30
        self.map_height = 30
        self.map_data = self.generate_30x30_map()
        
        self.tile_size = 16
        
        # マップ全体のピクセルサイズ
        self.map_pixel_width = self.map_width * self.tile_size
        self.map_pixel_height = self.map_height * self.tile_size
        
        # ホバー情報表示
        self.hover_info = HoverInfo()

    def generate_30x30_map(self):
        """30x30のマップを生成"""
        map_data = []
        for row in range(30):
            map_row = []
            for col in range(30):
                # 外周は壁
                if row == 0 or row == 29 or col == 0 or col == 29:
                    map_row.append(1)
                # 内部にランダムに壁を配置
                elif (row % 4 == 0 and col % 4 == 0) or (row % 6 == 2 and col % 6 == 2):
                    map_row.append(1)
                # 特定のパターンで壁を配置
                elif (row % 8 == 3 and col % 3 == 1) or (row % 5 == 1 and col % 7 == 4):
                    map_row.append(1)
                else:
                    map_row.append(0)
            map_data.append(map_row)
        return map_data

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
            target_camera_x = max(0, min(target_camera_x, self.map_pixel_width - screen_width))
            target_camera_y = max(0, min(target_camera_y, self.map_pixel_height - screen_height))
            
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
            city_name = city.name
        else:
            city_name = city
            
        connected_names = self.game_state.get_connected_city_names(city_name)
        return [self.game_state.get_city_by_name(name) for name in connected_names if self.game_state.get_city_by_name(name)]
    
    def get_distance_to_nearest_player(self, enemy_city):
        """指定したCityから最も近いプレイヤーまでの距離を計算"""
        min_distance = float('inf')
        nearest_player = None
        
        for player in self.game_state.players:
            if player.current_city_name:
                player_city = self.game_state.get_city_by_name(player.current_city_name)
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
        
        # 都市名で処理
        start_name = start_city.name if isinstance(start_city, City) else start_city
        target_name = target_city.name if isinstance(target_city, City) else target_city
        
        if start_name == target_name:
            return []
        
        # BFS for pathfinding
        queue = [(start_name, [])]
        visited = {start_name}
        
        while queue:
            current_city_name, path = queue.pop(0)
            
            for connected_city_name in self.game_state.get_connected_city_names(current_city_name):
                if connected_city_name == target_name:
                    result_cities = []
                    for city_name in path + [connected_city_name]:
                        city = self.game_state.get_city_by_name(city_name)
                        if city:
                            result_cities.append(city)
                    return result_cities
                
                if connected_city_name not in visited:
                    visited.add(connected_city_name)
                    queue.append((connected_city_name, path + [connected_city_name]))
        
        return []  # No path found
    
    def decide_enemy_action(self, enemy):
        """敵のAIに基づいて行動を決定"""
        if not enemy.current_city_name:
            return None
        
        current_city = self.game_state.get_city_by_name(enemy.current_city_name)
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
            min_distance, nearest_player = self.get_distance_to_nearest_player(current_city)
            
            if nearest_player and nearest_player.current_city_name:
                nearest_player_city = self.game_state.get_city_by_name(nearest_player.current_city_name)
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
            min_distance, nearest_player = self.get_distance_to_nearest_player(current_city)
            
            if nearest_player and nearest_player.current_city_name:
                nearest_player_city = self.game_state.get_city_by_name(nearest_player.current_city_name)
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
            if enemy.patrol_city_names and len(enemy.patrol_city_names) > 1:
                # 次のパトロール地点を取得
                next_index = (enemy.patrol_index + 1) % len(enemy.patrol_city_names)
                target_city_name = enemy.patrol_city_names[next_index]
                target_city = self.game_state.get_city_by_name(target_city_name)
                
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
    
    def execute_enemy_ai_turn(self):
        """敵のAIターンを実行"""
        if self.game_state.current_turn != "enemy" or self.game_state.enemy_moved_this_turn:
            return
        
        # まだ移動していない敵を選択
        available_enemies = [enemy for enemy in self.game_state.enemies if not enemy.is_moving]
        if not available_enemies:
            return
        
        # ランダムに敵を選択
        selected_enemy = random.choice(available_enemies)
        selected_enemy_index = self.game_state.enemies.index(selected_enemy)
        self.game_state.current_ai_enemy_index = selected_enemy_index  # 現在AI処理中の敵を記録
        
        # 敵を選択時にカメラ追従を設定
        self.set_camera_follow_target(selected_enemy)
        
        # AIに基づいて移動先を決定
        target_city = self.decide_enemy_action(selected_enemy)
        
        if target_city and self.game_state.are_cities_connected(selected_enemy.current_city_name, target_city.name):
            # 移動実行
            selected_enemy.target_x = target_city.x
            selected_enemy.target_y = target_city.y
            selected_enemy.target_city_name = target_city.name
            selected_enemy.is_moving = True
            self.game_state.enemy_moved_this_turn = True
            
            # パトロールAIの場合はインデックスを更新
            if selected_enemy.ai_type == "patrol" and target_city.name in selected_enemy.patrol_city_names:
                selected_enemy.patrol_index = selected_enemy.patrol_city_names.index(target_city.name)
        
        self.game_state.current_ai_enemy_index = None  # AI処理完了

    def get_character_positions_by_city(self):
        """各Cityにいるキャラクターを収集して辞書で返す"""
        character_positions = {}
        for city_name, city in self.game_state.cities.items():
            character_positions[city] = []
            for player in self.game_state.players:
                if player.current_city_name == city_name:
                    character_positions[city].append(('player', player))
            for enemy in self.game_state.enemies:
                if enemy.current_city_name == city_name:
                    character_positions[city].append(('enemy', enemy))
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
            if player.current_city_name and not player.is_moving:
                # 移動中でない場合のみオフセットを適用
                current_city = self.game_state.get_city_by_name(player.current_city_name)
                if current_city and current_city in character_positions:
                    city_characters = character_positions[current_city]
                    char_index = next((idx for idx, (char_type, char) in enumerate(city_characters) 
                                     if char_type == 'player' and char == player), 0)
                    
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
            if (adjusted_x - half_width <= world_x <= adjusted_x + half_width and
                player.y - half_height <= world_y <= player.y + half_height):
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
            if (city.x - half_size <= world_x <= city.x + half_size and
                city.y - half_size <= world_y <= city.y + half_size):
                return city
        return None
        
    def get_player_current_city(self, player):
        """プレイヤーが現在いるCityを取得"""
        if player.current_city_name:
            return self.game_state.get_city_by_name(player.current_city_name)
        return None
        
    def is_cities_connected(self, city1, city2):
        """2つのCity間がRoadで接続されているかチェック"""
        city1_name = city1.name if isinstance(city1, City) else city1
        city2_name = city2.name if isinstance(city2, City) else city2
        return self.game_state.are_cities_connected(city1_name, city2_name)
    
    def line_intersects_screen(self, x1, y1, x2, y2):
        """線分が画面と交差するかチェック"""
        # 画面の境界
        screen_left = 0
        screen_right = screen_width
        screen_top = 0
        screen_bottom = screen_height
        
        # 両端点が画面内にある場合
        if (screen_left <= x1 <= screen_right and screen_top <= y1 <= screen_bottom) or \
           (screen_left <= x2 <= screen_right and screen_top <= y2 <= screen_bottom):
            return True
        
        # 線分のバウンディングボックスが画面と交差するかチェック
        line_left = min(x1, x2)
        line_right = max(x1, x2)
        line_top = min(y1, y2)
        line_bottom = max(y1, y2)
        
        # バウンディングボックスが画面と重複しない場合は交差しない
        if line_right < screen_left or line_left > screen_right or \
           line_bottom < screen_top or line_top > screen_bottom:
            return False
        
        # より詳細な線分交差判定（線分が画面境界と交差するかチェック）
        return (self.line_intersects_line(x1, y1, x2, y2, screen_left, screen_top, screen_right, screen_top) or   # 上辺
                self.line_intersects_line(x1, y1, x2, y2, screen_right, screen_top, screen_right, screen_bottom) or # 右辺
                self.line_intersects_line(x1, y1, x2, y2, screen_right, screen_bottom, screen_left, screen_bottom) or # 下辺
                self.line_intersects_line(x1, y1, x2, y2, screen_left, screen_bottom, screen_left, screen_top))      # 左辺
    
    def line_intersects_line(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """2つの線分が交差するかチェック"""
        def ccw(ax, ay, bx, by, cx, cy):
            return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)
        return ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and \
               ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4)

    def start_battle_sequence(self, battle_results):
        """戦闘シーケンスを開始"""
        if not battle_results:
            return
            
        self.pending_battle_results = battle_results
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
        city_name = current_battle['city_name']
        city = self.game_state.get_city_by_name(city_name)
        
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
        target_camera_x = max(0, min(target_camera_x, self.map_pixel_width - screen_width))
        target_camera_y = max(0, min(target_camera_y, self.map_pixel_height - screen_height))
        
        # カメラ位置を即座に設定（アニメーションなしで即移動）
        self.camera_x = target_camera_x
        self.camera_y = target_camera_y
        
        # カメラ追従をクリア
        self.clear_camera_follow()
    
    def start_current_battle_scene(self):
        """現在の戦闘のBattleSubSceneを開始"""
        current_battle = self.pending_battle_results[self.current_battle_index]
        city_name = current_battle['city_name']
        city = self.game_state.get_city_by_name(city_name)
        
        if city:
            # BattleSubSceneを開始
            battle_sub_scene = BattleSubScene(self, current_battle, city)
            self.set_sub_scene(battle_sub_scene)
    
    def on_battle_scene_finished(self):
        """戦闘シーンが終了した時の処理"""
        self.current_battle_index += 1
        
        if self.current_battle_index < len(self.pending_battle_results):
            # 次の戦闘を処理
            self.process_next_battle()
        else:
            # 全ての戦闘処理が完了
            self.finish_battle_sequence()
    
    def finish_battle_sequence(self):
        """戦闘シーケンスを終了"""
        self.is_processing_battles = False
        self.pending_battle_results = []
        self.current_battle_index = 0
        
        # 戦闘シーケンス完了後に倒されたキャラクターを削除
        self.game_state.remove_defeated_characters()
        
        # ターン切り替えのカットインを表示
        if self.game_state.current_turn == "player":
            cutin_text = "ENEMY TURN"
        else:
            cutin_text = "PLAYER TURN"
            
        self.set_sub_scene(CutinSubScene(self, cutin_text))

    def on_sub_scene_finished(self, finished_sub_scene):
        """サブシーン終了時の処理"""
        # BattleSubSceneが終了した場合
        if isinstance(finished_sub_scene, BattleSubScene):
            self.on_battle_scene_finished()

    def switch_turn(self):
        """ターンを切り替える"""
        # ターン終了時に戦闘をチェック・実行
        battle_results = self.game_state.check_and_execute_battles()
        
        # ターン状態を更新
        if self.game_state.current_turn == "player":
            self.game_state.current_turn = "enemy"
            self.game_state.player_moved_this_turn = False
            self.selected_player = None  # プレイヤー選択を解除
            self.game_state.ai_timer = 0  # AIタイマーをリセット
            # プレイヤーターンからエネミーターンに切り替わる際はカメラ追従をクリア
            self.clear_camera_follow()
        else:
            self.game_state.current_turn = "player"
            self.game_state.enemy_moved_this_turn = False
            self.selected_enemy = None  # 敵選択を解除
            self.game_state.turn_counter += 1  # プレイヤーターンの開始で新しいターン番号
            self.game_state.ai_timer = 0  # AIタイマーをリセット
            # エネミーターンからプレイヤーターンに切り替わる際はカメラ追従をクリア
            self.clear_camera_follow()
        
        # 戦闘結果がある場合は戦闘シーケンスを開始
        if battle_results:
            self.start_battle_sequence(battle_results)
        else:
            # 戦闘がない場合でも倒されたキャラクターがいる可能性があるので削除処理を実行
            self.game_state.remove_defeated_characters()
            
            # 戦闘がない場合は通常のターン切り替えカットイン
            if self.game_state.current_turn == "player":
                cutin_text = "PLAYER TURN"
            else:
                cutin_text = "ENEMY TURN"
            
            self.set_sub_scene(CutinSubScene(self, cutin_text))
        
        # ターン切り替え時に自動セーブ
        self.game_state.auto_save()
    
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
            if enemy.current_city_name and not enemy.is_moving:
                # 移動中でない場合のみオフセットを適用
                current_city = self.game_state.get_city_by_name(enemy.current_city_name)
                if current_city and current_city in character_positions:
                    city_characters = character_positions[current_city]
                    char_index = next((idx for idx, (char_type, char) in enumerate(city_characters) 
                                     if char_type == 'enemy' and char == enemy), 0)
                    
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
            if (adjusted_x - half_width <= world_x <= adjusted_x + half_width and
                enemy.y - half_height <= world_y <= enemy.y + half_height):
                return enemy
        return None

    def update(self):
        # サブシーンの処理を先に実行
        if super().update():
            return self
        
        # 戦闘処理中の場合
        if self.is_processing_battles:
            # Qキーでタイトルシーンに戻ることは可能
            if pyxel.btnp(pyxel.KEY_Q):
                from game import TitleScene
                return TitleScene()
                
            # カメラ移動後の待機時間
            if hasattr(self, 'battle_camera_timer'):
                self.battle_camera_timer -= 1
                if self.battle_camera_timer <= 0:
                    delattr(self, 'battle_camera_timer')
                    self.start_current_battle_scene()
            return self
        
        # メインの処理
        # Qキーでタイトルシーンに戻る
        if pyxel.btnp(pyxel.KEY_Q):
            from game import TitleScene
            return TitleScene()
        
        # ESCキーでプレイヤー選択を解除
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            if self.game_state.current_turn == "player":
                self.selected_player = None
            else:
                self.selected_enemy = None
            
        # Vキーでデバッグ情報のページ切り替え
        if pyxel.btnp(pyxel.KEY_V):
            self.debug_page = (self.debug_page + 1) % (self.max_debug_page + 1)
            
        # Spaceキーでターンスキップ
        if pyxel.btnp(pyxel.KEY_SPACE):
            if not any(player.is_moving for player in self.game_state.players) and \
               not any(enemy.is_moving for enemy in self.game_state.enemies):
                self.switch_turn()
        
        # 敵のAI処理（エネミーターン時）
        if self.game_state.current_turn == "enemy" and self.can_move_this_turn():
            # 敵が移動していない場合のみAIタイマーを進める
            if not any(enemy.is_moving for enemy in self.game_state.enemies):
                self.game_state.ai_timer += 1
                
                # AI決定遅延時間が経過したら敵の行動を実行
                if self.game_state.ai_timer >= self.game_state.ai_decision_delay:
                    self.execute_enemy_ai_turn()
                    self.game_state.ai_timer = 0
        
        # マウスクリック検出
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.click_x = pyxel.mouse_x
            self.click_y = pyxel.mouse_y
            self.click_timer = 120  # 4秒間表示（30fps * 4秒）
            
            if self.game_state.current_turn == "player" and self.can_move_this_turn():
                # プレイヤーターン：プレイヤーとCityのクリック処理
                clicked_player = self.get_player_at_position(self.click_x, self.click_y)
                clicked_city = self.get_city_at_position(self.click_x, self.click_y)
                
                if clicked_player:
                    # プレイヤーを選択
                    self.selected_player = clicked_player
                elif clicked_city and self.selected_player:
                    # プレイヤーの現在位置のCityを取得
                    current_city = self.get_player_current_city(self.selected_player)
                    
                    if current_city and self.is_cities_connected(current_city, clicked_city):
                        # 接続されているCityにのみ移動可能
                        self.selected_player.target_x = clicked_city.x
                        self.selected_player.target_y = clicked_city.y
                        self.selected_player.target_city_name = clicked_city.name
                        self.selected_player.is_moving = True
                        self.game_state.player_moved_this_turn = True
                        # プレイヤー移動時に自動セーブ
                        self.game_state.auto_save()
                    elif current_city and current_city != clicked_city:
                        # 接続されていないCityへの移動は拒否
                        pass
                    elif current_city == clicked_city:
                        # 同じCityをクリックした場合は移動しない
                        pass
            
            elif self.game_state.current_turn == "enemy" and self.can_move_this_turn():
                # エネミーターン：敵とCityのクリック処理
                clicked_enemy = self.get_enemy_at_position(self.click_x, self.click_y)
                clicked_city = self.get_city_at_position(self.click_x, self.click_y)
                
                if clicked_enemy:
                    # 敵を選択
                    self.selected_enemy = clicked_enemy
                    # 敵を選択時にカメラ追従を設定
                    self.set_camera_follow_target(clicked_enemy)
                elif clicked_city and self.selected_enemy:
                    # 敵の現在位置のCityを取得
                    current_city = self.game_state.get_city_by_name(self.selected_enemy.current_city_name) if self.selected_enemy.current_city_name else None
                    
                    if current_city and self.is_cities_connected(current_city, clicked_city):
                        # 接続されているCityにのみ移動可能
                        self.selected_enemy.target_x = clicked_city.x
                        self.selected_enemy.target_y = clicked_city.y
                        self.selected_enemy.target_city_name = clicked_city.name
                        self.selected_enemy.is_moving = True
                        self.game_state.enemy_moved_this_turn = True
                        # 敵移動時に自動セーブ
                        self.game_state.auto_save()
                    elif current_city and current_city != clicked_city:
                        # 接続されていないCityへの移動は拒否
                        pass
                    elif current_city == clicked_city:
                        # 同じCityをクリックした場合は移動しない
                        pass
        
        # クリック座標表示時間を減らす
        if self.click_timer > 0:
            self.click_timer -= 1

        # プレイヤーの移動処理
        for player in self.game_state.players:
            if player.is_moving and player.target_x is not None and player.target_y is not None:
                # 目標地点への移動ベクトルを計算
                dx = player.target_x - player.x
                dy = player.target_y - player.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                # 移動方向に基づいて向きを更新
                if abs(dx) > 1:  # 横方向の移動が十分大きい場合のみ向きを変更
                    player.facing_right = dx > 0
                
                if distance <= player.speed:
                    # 目標地点に到達
                    player.x = player.target_x
                    player.y = player.target_y
                    player.current_city_name = player.target_city_name  # 現在位置Cityを更新
                    player.is_moving = False
                    player.target_x = None
                    player.target_y = None
                    player.target_city_name = None
                    # プレイヤーの移動完了時にターン切り替え
                    if self.game_state.current_turn == "player":
                        self.switch_turn()
                else:
                    # 目標地点に向かって移動
                    player.x += (dx / distance) * player.speed
                    player.y += (dy / distance) * player.speed
        
        # 敵の移動処理
        for enemy in self.game_state.enemies:
            if enemy.is_moving and enemy.target_x is not None and enemy.target_y is not None:
                # 目標地点への移動ベクトルを計算
                dx = enemy.target_x - enemy.x
                dy = enemy.target_y - enemy.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                # 移動方向に基づいて向きを更新
                if abs(dx) > 1:  # 横方向の移動が十分大きい場合のみ向きを変更
                    enemy.facing_right = dx > 0
                
                if distance <= enemy.speed:
                    # 目標地点に到達
                    enemy.x = enemy.target_x
                    enemy.y = enemy.target_y
                    enemy.current_city_name = enemy.target_city_name  # 現在位置Cityを更新
                    enemy.is_moving = False
                    enemy.target_x = None
                    enemy.target_y = None
                    enemy.target_city_name = None
                    # 敵の移動完了時にターン切り替え
                    if self.game_state.current_turn == "enemy":
                        self.switch_turn()
                else:
                    # 目標地点に向かって移動
                    enemy.x += (dx / distance) * enemy.speed
                    enemy.y += (dy / distance) * enemy.speed
            
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
        self.camera_y = max(0, min(self.camera_y, self.map_pixel_height - screen_height))
        
        # ゲーム終了条件をチェック
        if not self.game_state.players:
            # 全プレイヤーが倒された場合
            pyxel.text(screen_width // 2 - 30, screen_height // 2, "GAME OVER", 8)
            pyxel.text(screen_width // 2 - 40, screen_height // 2 + 10, "Press Q to return to title", 7)
        elif not self.game_state.enemies:
            # 全敵が倒された場合
            pyxel.text(screen_width // 2 - 20, screen_height // 2, "VICTORY!", 11)
            pyxel.text(screen_width // 2 - 40, screen_height // 2 + 10, "Press Q to return to title", 7)
        
        return self


    def draw(self):
        # サブシーンがある場合はサブシーンを描画
        if super().draw():
            return
        
        # メインの描画
        pyxel.cls(3)  # 背景色
        
        # 画面に表示するタイルの範囲を計算
        start_col = int(self.camera_x // self.tile_size)
        end_col = min(int((self.camera_x + screen_width) // self.tile_size) + 1, self.map_width)
        start_row = int(self.camera_y // self.tile_size)
        end_row = min(int((self.camera_y + screen_height) // self.tile_size) + 1, self.map_height)
        
        # マップを描画（カメラ位置を考慮）
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if 0 <= row < self.map_height and 0 <= col < self.map_width:
                    x = col * self.tile_size - self.camera_x
                    y = row * self.tile_size - self.camera_y
                    
                    if self.map_data[row][col] == 1:
                        # 壁（茶色）
                        pyxel.rect(x, y, self.tile_size, self.tile_size, 4)
                    else:
                        # 床（薄い色）
                        pyxel.rect(x, y, self.tile_size, self.tile_size, 6)
        
        # 道路を描画（Cityよりも先に描画して背景に）
        for road in self.game_state.roads:
            city1 = self.game_state.get_city_by_name(road.city1_name)
            city2 = self.game_state.get_city_by_name(road.city2_name)
            
            if city1 and city2:
                city1_screen_x = city1.x - self.camera_x
                city1_screen_y = city1.y - self.camera_y
                city2_screen_x = city2.x - self.camera_x
                city2_screen_y = city2.y - self.camera_y
                
                # 線分が画面と交差するかチェック（より正確な判定）
                if self.line_intersects_screen(city1_screen_x, city1_screen_y, city2_screen_x, city2_screen_y):
                    pyxel.line(city1_screen_x, city1_screen_y, city2_screen_x, city2_screen_y, 9)  # オレンジ色の線
        
        # Cityを描画
        for city_name, city in self.game_state.cities.items():
            city_screen_x = city.x - self.camera_x
            city_screen_y = city.y - self.camera_y
            
            # Cityが画面内にある場合のみ描画
            if (-city.size <= city_screen_x <= screen_width + city.size and
                -city.size <= city_screen_y <= screen_height + city.size):
                
                half_size = city.size // 2
                # City本体（青色の円）
                pyxel.circb(city_screen_x, city_screen_y, half_size, 12)  # 青色の枠
                pyxel.circ(city_screen_x, city_screen_y, half_size - 2, 1)  # 濃い青の内部
                
                # City名前を表示
                text_x = city_screen_x - len(city.name) * 2
                text_y = city_screen_y + half_size + 2
                pyxel.text(text_x, text_y, city.name, 7)  # 白文字

        # キャラクターの描画位置を計算（重なりを防ぐ）
        character_positions = self.get_character_positions_by_city()  # City毎にキャラクターのリストを管理

        # プレイヤーを描画（カメラ位置を考慮、重なり防止）
        for i, player in enumerate(self.game_state.players):
            # キャラクターの描画位置を計算
            if player.current_city_name and not player.is_moving:
                # 移動中でない場合のみ同じCity内での位置調整を行う
                current_city = self.game_state.get_city_by_name(player.current_city_name)
                if current_city and current_city in character_positions:
                    city_characters = character_positions[current_city]
                    char_index = next((idx for idx, (char_type, char) in enumerate(city_characters) 
                                     if char_type == 'player' and char == player), 0)
                    
                    # 複数キャラクターがいる場合は横に並べる
                    offset_x = 0
                    if len(city_characters) > 1:
                        total_width = len(city_characters) * player.width
                        start_x = -(total_width - player.width) // 2
                        offset_x = start_x + char_index * player.width
                    
                    player_screen_x = player.x + offset_x - self.camera_x
                else:
                    player_screen_x = player.x - self.camera_x
            else:
                # 移動中または現在のCityがない場合はオフセットなし
                player_screen_x = player.x - self.camera_x
                
            player_screen_y = player.y - self.camera_y
            
            # プレイヤーが画面内にある場合のみ描画
            if (-player.width <= player_screen_x <= screen_width + player.width and
                -player.height <= player_screen_y <= screen_height + player.height):
                # プレイヤーキャラクター（resources.pyxresのImage0、image_indexに基づく段を使用）
                half_width = player.width // 2
                half_height = player.height // 2
                
                # アニメーションフレームを計算（2つのフレームを交互に表示）
                anim_frame = (pyxel.frame_count // 10) % 2
                src_x = anim_frame * 16  # 0または16
                src_y = player.image_index * 16  # image_indexに基づいてY座標を計算
                
                # 向いている方向に応じて描画幅を調整（右向きの場合は負の値で反転）
                draw_width = player.width if not player.facing_right else -player.width
                
                pyxel.blt(
                    int(player_screen_x - half_width), 
                    int(player_screen_y - half_height), 
                    0,  # Image Bank 0
                    src_x,  # ソース画像のX座標（0または16）
                    src_y,  # ソース画像のY座標（image_indexに基づく）
                    draw_width, # 幅（負の値で左右反転）
                    player.height, # 高さ
                    2   # 透明色（紫色を透明にする）
                )
                
                # ライフゲージを表示
                life_bar_width = player.width
                life_bar_height = 3
                life_bar_x = int(player_screen_x - half_width)
                life_bar_y = int(player_screen_y - half_height - 8)
                
                # ライフゲージの背景（赤色）
                pyxel.rect(life_bar_x, life_bar_y, life_bar_width, life_bar_height, 8)
                
                # ライフゲージの現在値（緑色）
                current_life_width = int((player.life / player.max_life) * life_bar_width)
                if current_life_width > 0:
                    pyxel.rect(life_bar_x, life_bar_y, current_life_width, life_bar_height, 11)
                
                # 選択されたプレイヤーに点滅する枠線を描画
                if player == self.selected_player:
                    # 点滅効果（30フレームで1回点滅）
                    if (pyxel.frame_count // 10) % 3 != 0:                        # 枠線の色（明るい色で目立つように）
                        frame_color = 11  # ライトブルー
                        
                        # 枠線を描画
                        frame_x = int(player_screen_x - half_width - 1)
                        frame_y = int(player_screen_y - half_height - 1)
                        frame_w = player.width + 2
                        frame_h = player.height + 2
                        
                        # 上下の線
                        pyxel.rect(frame_x, frame_y, frame_w, 1, frame_color)
                        pyxel.rect(frame_x, frame_y + frame_h - 1, frame_w, 1, frame_color)
                        # 左右の線
                        pyxel.rect(frame_x, frame_y, 1, frame_h, frame_color)
                        pyxel.rect(frame_x + frame_w - 1, frame_y, 1, frame_h, frame_color)

        # 敵キャラクターを描画（カメラ位置を考慮、重なり防止）
        for i, enemy in enumerate(self.game_state.enemies):
            # キャラクターの描画位置を計算
            if enemy.current_city_name and not enemy.is_moving:
                # 移動中でない場合のみ同じCity内での位置調整を行う
                current_city = self.game_state.get_city_by_name(enemy.current_city_name)
                if current_city and current_city in character_positions:
                    city_characters = character_positions[current_city]
                    char_index = next((idx for idx, (char_type, char) in enumerate(city_characters) 
                                     if char_type == 'enemy' and char == enemy), 0)
                    
                    # 複数キャラクターがいる場合は横に並べる
                    offset_x = 0
                    if len(city_characters) > 1:
                        total_width = len(city_characters) * enemy.width
                        start_x = -(total_width - enemy.width) // 2
                        offset_x = start_x + char_index * enemy.width
                    
                    enemy_screen_x = enemy.x + offset_x - self.camera_x
                else:
                    enemy_screen_x = enemy.x - self.camera_x
            else:
                # 移動中または現在のCityがない場合はオフセットなし
                enemy_screen_x = enemy.x - self.camera_x
                
            enemy_screen_y = enemy.y - self.camera_y
            
            # 敵が画面内にある場合のみ描画
            if (-enemy.width <= enemy_screen_x <= screen_width + enemy.width and
                -enemy.height <= enemy_screen_y <= screen_height + enemy.height):
                # 敵キャラクター（resources.pyxresのImage0、image_indexに基づく段を使用）
                half_width = enemy.width // 2
                half_height = enemy.height // 2
                
                # アニメーションフレームを計算（2つのフレームを交互に表示）
                anim_frame = (pyxel.frame_count // 10) % 2
                src_x = anim_frame * 16  # 0または16
                src_y = enemy.image_index * 16  # image_indexに基づいてY座標を計算
                
                # 向いている方向に応じて描画幅を調整（右向きの場合は負の値で反転）
                draw_width = enemy.width if not enemy.facing_right else -enemy.width
                
                pyxel.blt(
                    int(enemy_screen_x - half_width), 
                    int(enemy_screen_y - half_height), 
                    0,  # Image Bank 0
                    src_x,  # ソース画像のX座標（0または16）
                    src_y,  # ソース画像のY座標（image_indexに基づく）
                    draw_width, # 幅（負の値で左右反転）
                    enemy.height, # 高さ
                    2   # 透明色（紫色を透明にする）
                )
                
                # ライフゲージを表示
                life_bar_width = enemy.width
                life_bar_height = 3
                life_bar_x = int(enemy_screen_x - half_width)
                life_bar_y = int(enemy_screen_y - half_height - 8)
                
                # ライフゲージの背景（赤色）
                pyxel.rect(life_bar_x, life_bar_y, life_bar_width, life_bar_height, 8)
                
                # ライフゲージの現在値（緑色）
                current_life_width = int((enemy.life / enemy.max_life) * life_bar_width)
                if current_life_width > 0:
                    pyxel.rect(life_bar_x, life_bar_y, current_life_width, life_bar_height, 11)
                
                  # AI種別インジケーターを表示（敵の上に小さな色付きの円）
                indicator_x = int(enemy_screen_x)
                indicator_y = int(enemy_screen_y - half_height - 6)
                
                if enemy.ai_type == "aggressive":
                    pyxel.circ(indicator_x, indicator_y, 2, 8)  # 赤色
                elif enemy.ai_type == "patrol":
                    pyxel.circ(indicator_x, indicator_y, 2, 11)  # ライトブルー  
                elif enemy.ai_type == "defensive":
                    pyxel.circ(indicator_x, indicator_y, 2, 3)  # 緑色
                else:  # random
                    pyxel.circ(indicator_x, indicator_y, 2, 14)  # ピンク
                
                # AI思考中のインジケーター（エネミーターン時にAIタイマーが動いている間）
                current_ai_enemy = None
                if (self.game_state.current_ai_enemy_index is not None and 
                    0 <= self.game_state.current_ai_enemy_index < len(self.game_state.enemies)):
                    current_ai_enemy = self.game_state.enemies[self.game_state.current_ai_enemy_index]
                
                if (self.game_state.current_turn == "enemy" and self.game_state.ai_timer > 0 and 
                    enemy == current_ai_enemy):
                    # 点滅する思考インジケーター
                    if (pyxel.frame_count // 5) % 2 == 0:
                        pyxel.circ(int(enemy_screen_x), int(enemy_screen_y - half_height - 12), 3, 7)  # 白色の思考バブル
                
                # 選択された敵に点滅する枠線を描画（エネミーターン時）
                if enemy == self.selected_enemy and self.game_state.current_turn == "enemy":
                    # 点滅効果（30フレームで1回点滅）
                    if (pyxel.frame_count // 10) % 3 != 0:
                        frame_color = 8  # 赤色
                        
                        # 枠線を描画
                        frame_x = int(enemy_screen_x - half_width - 1)
                        frame_y = int(enemy_screen_y - half_height - 1)
                        frame_w = enemy.width + 2
                        frame_h = enemy.height + 2
                        
                        # 上下の線
                        pyxel.rect(frame_x, frame_y, frame_w, 1, frame_color)
                        pyxel.rect(frame_x, frame_y + frame_h - 1, frame_w, 1, frame_color)
                        # 左右の線
                        pyxel.rect(frame_x, frame_y, 1, frame_h, frame_color)
                        pyxel.rect(frame_x + frame_w - 1, frame_y, 1, frame_h, frame_color)
        # UI表示
        # ホバー情報の表示（最優先で表示）
        mouse_x = pyxel.mouse_x
        mouse_y = pyxel.mouse_y
        hovered_character = self.get_player_at_position(mouse_x, mouse_y)
        if not hovered_character:
            hovered_character = self.get_enemy_at_position(mouse_x, mouse_y)
        hovered_city = self.get_city_at_position(mouse_x, mouse_y)
        
        self.hover_info.draw_hover_info(mouse_x, mouse_y, hovered_character, hovered_city)
        
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
            turn_text = f"Turn {self.game_state.turn_counter}: {self.game_state.current_turn.upper()} TURN"
            turn_color = 11 if self.game_state.current_turn == "player" else 8
            pyxel.text(5, 45, turn_text, turn_color)
            
            can_move = "YES" if self.can_move_this_turn() else "NO"
            move_text = f"Can move this turn: {can_move}"
            pyxel.text(5, 55, move_text, 10)
            
            # 選択中のキャラクター情報を表示
            if self.game_state.current_turn == "player" and self.selected_player:
                current_city_name = self.selected_player.current_city_name if self.selected_player.current_city_name else "None"
                selected_text = f"Selected Player at {current_city_name}:"
                pyxel.text(5, 65, selected_text, 11)
                pos_text = f"  Position: ({int(self.selected_player.x)}, {int(self.selected_player.y)})"
                pyxel.text(5, 75, pos_text, 11)
                # プレイヤーの戦闘ステータスを表示
                status_text = f"  Life: {self.selected_player.life}/{self.selected_player.max_life}, Attack: {self.selected_player.attack}"
                pyxel.text(5, 85, status_text, 11)
            elif self.game_state.current_turn == "enemy" and self.selected_enemy:
                current_city_name = self.selected_enemy.current_city_name if self.selected_enemy.current_city_name else "None"
                selected_text = f"Selected Enemy at {current_city_name}:"
                pyxel.text(5, 65, selected_text, 8)
                pos_text = f"  Position: ({int(self.selected_enemy.x)}, {int(self.selected_enemy.y)})"
                pyxel.text(5, 75, pos_text, 8)
                # 敵の戦闘ステータスを表示
                status_text = f"  Life: {self.selected_enemy.life}/{self.selected_enemy.max_life}, Attack: {self.selected_enemy.attack}"
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
                follow_info = f"Camera following: {self.camera_follow_target.ai_type if hasattr(self.camera_follow_target, 'ai_type') else 'Player'}"
                pyxel.text(5, 35, follow_info, 13)
            else:
                pyxel.text(5, 35, "Camera: Manual control", 6)
                
            # Cities情報を表示
            pyxel.text(5, 50, "Cities:", 14)
            y_pos = 60
            for city_name, city in self.game_state.cities.items():
                if y_pos > screen_height - 10:  # 画面からはみ出さないように制限
                    break
                city_info = f"{city.name}: ({int(city.x)}, {int(city.y)})"
                pyxel.text(5, y_pos, city_info, 12)
                y_pos += 10
                
        elif page == 3:
            # ページ3: キャラクター情報とAI情報
            pyxel.text(5, 15, "Characters & AI Information", 14)
            
            # プレイヤーの情報を表示
            pyxel.text(5, 25, "Players:", 14)
            y_pos = 35
            for i, player in enumerate(self.game_state.players):
                player_city_name = player.current_city_name if player.current_city_name else "None"
                player_info = f"Player {i+1} at {player_city_name}: Life {player.life}/{player.max_life}"
                pyxel.text(5, y_pos, player_info, 11)
                y_pos += 10
            
            # 敵の情報を表示
            y_pos += 5
            pyxel.text(5, y_pos, "Enemies:", 14)
            y_pos += 10
            for i, enemy in enumerate(self.game_state.enemies):
                enemy_city_name = enemy.current_city_name if enemy.current_city_name else "None"
                enemy_info = f"Enemy {i+1} ({enemy.ai_type}) at {enemy_city_name}:"
                pyxel.text(5, y_pos, enemy_info, 8)
                y_pos += 10
                life_info = f"  Life {enemy.life}/{enemy.max_life}"
                pyxel.text(5, y_pos, life_info, 8)
                y_pos += 10
                
            # AI凡例を表示（画面の下部に）
            legend_y = screen_height - 35
            pyxel.text(5, legend_y, "AI Legend:", 14)
            pyxel.circ(15, legend_y + 8, 2, 8)   # 赤色
            pyxel.text(20, legend_y + 6, "Aggressive", 7)
            pyxel.circ(80, legend_y + 8, 2, 11)  # ライトブルー  
            pyxel.text(85, legend_y + 6, "Patrol", 7)
            pyxel.circ(15, legend_y + 16, 2, 3)   # 緑色
            pyxel.text(20, legend_y + 14, "Defensive", 7)
            pyxel.circ(80, legend_y + 16, 2, 14)  # ピンク
            pyxel.text(85, legend_y + 14, "Random", 7)
            
            # AI情報を表示（エネミーターン時）
            if self.game_state.current_turn == "enemy":
                ai_info = f"AI Timer: {self.game_state.ai_timer}/{self.game_state.ai_decision_delay}"
                pyxel.text(5, legend_y - 20, ai_info, 8)
            
            # 戦闘処理状態を表示
            if self.is_processing_battles:
                battle_info = f"Processing battles: {self.current_battle_index + 1}/{len(self.pending_battle_results)}"
                battle_y = legend_y - 30 if self.game_state.current_turn == "enemy" else legend_y - 20
                pyxel.text(5, battle_y, battle_info, 13)
            
            # マウスクリック座標を表示
            if self.click_timer > 0:
                coord_text = f"Click: ({self.click_x}, {self.click_y})"
                click_y = legend_y - 40 if (self.is_processing_battles and self.game_state.current_turn == "enemy") else \
                         legend_y - 30 if (self.is_processing_battles or self.game_state.current_turn == "enemy") else \
                         legend_y - 20
                pyxel.text(5, click_y, coord_text, 8)
                
            # 現在のマウス座標も表示
            mouse_text = f"Mouse: ({pyxel.mouse_x}, {pyxel.mouse_y})"
            mouse_y = click_y - 10 if self.click_timer > 0 else \
                     legend_y - 40 if (self.is_processing_battles and self.game_state.current_turn == "enemy") else \
                     legend_y - 30 if (self.is_processing_battles or self.game_state.current_turn == "enemy") else \
                     legend_y - 20
            pyxel.text(5, mouse_y, mouse_text, 10)
