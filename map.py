import pyxel
import math
import random

# game.pyから定数をインポート
from game import screen_width, screen_height, char_width, char_height, Scene

class City:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x  # ワールド座標（ピクセル）
        self.y = y  # ワールド座標（ピクセル）
        self.size = 20  # Cityの表示サイズ
        
class Road:
    def __init__(self, city1, city2):
        self.city1 = city1
        self.city2 = city2

class Character:
    def __init__(self, x, y, current_city=None, speed=1):
        self.x = x
        self.y = y
        self.width = char_width
        self.height = char_height
        self.speed = speed
        self.target_x = None  # 移動目標X座標
        self.target_y = None  # 移動目標Y座標
        self.target_city = None  # 移動目標City
        self.is_moving = False  # 移動中フラグ
        self.facing_right = True  # 向いている方向（True: 右, False: 左）
        self.current_city = current_city  # 現在位置のCity参照

class Player(Character):
    def __init__(self, x, y, current_city=None):
        super().__init__(x, y, current_city, speed=2)

class Enemy(Character):
    def __init__(self, x, y, current_city=None, ai_type="random"):
        super().__init__(x, y, current_city, speed=1)  # 敵の移動速度（プレイヤーより遅く設定）
        self.ai_type = ai_type  # AI behavior type: "random", "aggressive", "defensive", "patrol"
        self.patrol_cities = []  # For patrol AI - list of cities to patrol between
        self.patrol_index = 0   # Current index in patrol route
        self.last_player_position = None  # For tracking player movement

class MapScene(Scene):
    def __init__(self):
        self.click_x = -1  # クリック位置のX座標
        self.click_y = -1  # クリック位置のY座標
        self.click_timer = 0  # クリック座標表示時間
        self.selected_player = None  # 選択中のプレイヤー
        self.show_debug_info = True  # デバッグ情報表示フラグ
        
        # ターンベースシステム
        self.current_turn = "player"  # "player" または "enemy"
        self.turn_counter = 1  # ターン番号
        self.player_moved_this_turn = False  # このターンでプレイヤーが移動したか
        self.enemy_moved_this_turn = False  # このターンで敵が移動したか
        self.selected_enemy = None  # 選択中の敵（エネミーターン用）
        
        # カメラ位置（ビューの左上座標）
        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 4  # カメラの移動速度
        
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
        # Cityを定義（6つの街）
        self.cities = [
            City("Town A", 2 * self.tile_size, 2 * self.tile_size),      # 左上 (32, 32)
            City("Town B", 7 * self.tile_size, 2 * self.tile_size),      # 中上 (112, 32)
            City("Town C", 2 * self.tile_size, 6 * self.tile_size),      # 左下 (32, 96)
            City("Town D", 7 * self.tile_size, 6 * self.tile_size),      # 中下 (112, 96)
            City("Town E", 12 * self.tile_size, 2 * self.tile_size),     # 右上 (192, 32)
            City("Town F", 12 * self.tile_size, 6 * self.tile_size),     # 右下 (192, 96)
        ]
        # プレイヤーリスト（左端の2Cityに配置）
        self.players = [
            Player(self.cities[0].x, self.cities[0].y, self.cities[0]),  # プレイヤー1 → Town A
            Player(self.cities[2].x, self.cities[2].y, self.cities[2]),  # プレイヤー2 → Town C
        ]
        
        # 敵キャラクターリスト（右端の2Cityに配置）
        self.enemies = [
            Enemy(self.cities[4].x, self.cities[4].y, self.cities[4], "aggressive"),  # 敵1 → Town E (aggressive AI)
            Enemy(self.cities[5].x, self.cities[5].y, self.cities[5], "patrol"),     # 敵2 → Town F (patrol AI)
        ]
        
        # Patrol AI用のルートを設定
        self.enemies[1].patrol_cities = [self.cities[5], self.cities[3], self.cities[1], self.cities[4]]  # F->D->B->E循環
        
        # AI処理用のタイマー
        self.ai_timer = 0
        self.ai_decision_delay = 60  # 2秒間（30fps * 2秒）で敵が行動を決定
        self.current_ai_enemy = None  # 現在AI処理中の敵
        
        # City間の道路を定義
        self.roads = [
            Road(self.cities[0], self.cities[1]),  # Town A - Town B
            Road(self.cities[1], self.cities[4]),  # Town B - Town E
            Road(self.cities[0], self.cities[2]),  # Town A - Town C
            Road(self.cities[2], self.cities[3]),  # Town C - Town D
            Road(self.cities[3], self.cities[5]),  # Town D - Town F
            Road(self.cities[1], self.cities[3]),  # Town B - Town D
            Road(self.cities[4], self.cities[5]),  # Town E - Town F
            Road(self.cities[0], self.cities[3]),  # Town A - Town D (対角線)
            Road(self.cities[1], self.cities[5]),  # Town B - Town F (対角線)
        ]

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

    def get_connected_cities(self, city):
        """指定したCityに接続されているCityのリストを取得"""
        connected = []
        for road in self.roads:
            if road.city1 == city:
                connected.append(road.city2)
            elif road.city2 == city:
                connected.append(road.city1)
        return connected
    
    def get_distance_to_nearest_player(self, enemy_city):
        """指定したCityから最も近いプレイヤーまでの距離を計算"""
        min_distance = float('inf')
        nearest_player = None
        
        for player in self.players:
            if player.current_city:
                dx = player.current_city.x - enemy_city.x
                dy = player.current_city.y - enemy_city.y
                distance = (dx * dx + dy * dy) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    nearest_player = player
        
        return min_distance, nearest_player
    
    def find_path_to_target(self, start_city, target_city):
        """簡単なパス検索（BFS）で目標Cityへの最短経路を見つける"""
        if start_city == target_city:
            return []
        
        # BFS for pathfinding
        queue = [(start_city, [])]
        visited = {start_city}
        
        while queue:
            current_city, path = queue.pop(0)
            
            for connected_city in self.get_connected_cities(current_city):
                if connected_city == target_city:
                    return path + [connected_city]
                
                if connected_city not in visited:
                    visited.add(connected_city)
                    queue.append((connected_city, path + [connected_city]))
        
        return []  # No path found
    
    def decide_enemy_action(self, enemy):
        """敵のAIに基づいて行動を決定"""
        if not enemy.current_city:
            return None
        
        connected_cities = self.get_connected_cities(enemy.current_city)
        if not connected_cities:
            return None
        
        if enemy.ai_type == "random":
            # ランダムに接続されたCityから選択
            return random.choice(connected_cities)
        
        elif enemy.ai_type == "aggressive":
            # プレイヤーに近づこうとする行動
            min_distance, nearest_player = self.get_distance_to_nearest_player(enemy.current_city)
            
            if nearest_player and nearest_player.current_city:
                # プレイヤーに向かうパスを検索
                path = self.find_path_to_target(enemy.current_city, nearest_player.current_city)
                if path:
                    # パスの最初のステップに移動
                    return path[0]
            
            # プレイヤーが見つからない場合はランダム移動
            return random.choice(connected_cities)
        
        elif enemy.ai_type == "defensive":
            # プレイヤーから遠ざかろうとする行動
            min_distance, nearest_player = self.get_distance_to_nearest_player(enemy.current_city)
            
            if nearest_player and nearest_player.current_city:
                best_city = None
                max_distance = min_distance
                
                # 接続されたCityの中で最もプレイヤーから遠いCityを選択
                for city in connected_cities:
                    dx = nearest_player.current_city.x - city.x
                    dy = nearest_player.current_city.y - city.y
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
            if enemy.patrol_cities and len(enemy.patrol_cities) > 1:
                # 次のパトロール地点を取得
                next_index = (enemy.patrol_index + 1) % len(enemy.patrol_cities)
                target_city = enemy.patrol_cities[next_index]
                
                # 現在位置から次のパトロール地点への経路を検索
                path = self.find_path_to_target(enemy.current_city, target_city)
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
        if self.current_turn != "enemy" or self.enemy_moved_this_turn:
            return
        
        # まだ移動していない敵を選択
        available_enemies = [enemy for enemy in self.enemies if not enemy.is_moving]
        if not available_enemies:
            return
        
        # ランダムに敵を選択
        selected_enemy = random.choice(available_enemies)
        self.current_ai_enemy = selected_enemy  # 現在AI処理中の敵を記録
        
        # AIに基づいて移動先を決定
        target_city = self.decide_enemy_action(selected_enemy)
        
        if target_city and self.is_cities_connected(selected_enemy.current_city, target_city):
            # 移動実行
            selected_enemy.target_x = target_city.x
            selected_enemy.target_y = target_city.y
            selected_enemy.target_city = target_city
            selected_enemy.is_moving = True
            self.enemy_moved_this_turn = True
              # パトロールAIの場合はインデックスを更新
            if selected_enemy.ai_type == "patrol" and target_city in selected_enemy.patrol_cities:
                selected_enemy.patrol_index = selected_enemy.patrol_cities.index(target_city)
        
        self.current_ai_enemy = None  # AI処理完了
        if selected_enemy.ai_type == "patrol" and target_city in selected_enemy.patrol_cities:
            selected_enemy.patrol_index = selected_enemy.patrol_cities.index(target_city)

    def get_character_positions_by_city(self):
        """各Cityにいるキャラクターを収集して辞書で返す"""
        character_positions = {}
        for city in self.cities:
            character_positions[city] = []
            for player in self.players:
                if player.current_city == city:
                    character_positions[city].append(('player', player))
            for enemy in self.enemies:
                if enemy.current_city == city:
                    character_positions[city].append(('enemy', enemy))
        return character_positions

    def get_player_at_position(self, screen_x, screen_y):
        """指定したスクリーン座標にいるプレイヤーを取得"""
        # スクリーン座標をワールド座標に変換
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y
        
        # 各Cityにいるキャラクターを収集
        character_positions = self.get_character_positions_by_city()
        
        for player in self.players:
            # キャラクターの描画位置を計算（重なり防止と同じロジック）
            if player.current_city and not player.is_moving:
                # 移動中でない場合のみオフセットを適用
                city_characters = character_positions[player.current_city]
                char_index = next((idx for idx, (char_type, char) in enumerate(city_characters) 
                                 if char_type == 'player' and char == player), 0)
                
                offset_x = 0
                if len(city_characters) > 1:
                    total_width = len(city_characters) * player.width
                    start_x = -(total_width - player.width) // 2
                    offset_x = start_x + char_index * player.width
                
                adjusted_x = player.x + offset_x
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
        
        for city in self.cities:
            # Cityの範囲内かチェック
            half_size = city.size // 2
            if (city.x - half_size <= world_x <= city.x + half_size and
                city.y - half_size <= world_y <= city.y + half_size):
                return city
        return None
        
    def get_player_current_city(self, player):
        """プレイヤーが現在いるCityを取得"""
        return player.current_city
        
    def is_cities_connected(self, city1, city2):
        """2つのCity間がRoadで接続されているかチェック"""
        for road in self.roads:
            if (road.city1 == city1 and road.city2 == city2) or \
               (road.city1 == city2 and road.city2 == city1):
                return True
        return False
    
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

    def switch_turn(self):
        """ターンを切り替える"""
        if self.current_turn == "player":
            self.current_turn = "enemy"
            self.player_moved_this_turn = False
            self.selected_player = None  # プレイヤー選択を解除
            self.ai_timer = 0  # AIタイマーをリセット
        else:
            self.current_turn = "player"
            self.enemy_moved_this_turn = False
            self.selected_enemy = None  # 敵選択を解除
            self.turn_counter += 1  # プレイヤーターンの開始で新しいターン番号
            self.ai_timer = 0  # AIタイマーをリセット
    
    def can_move_this_turn(self):
        """このターンで移動可能かチェック"""
        if self.current_turn == "player":
            return not self.player_moved_this_turn
        else:
            return not self.enemy_moved_this_turn
    
    def get_enemy_at_position(self, screen_x, screen_y):
        """指定したスクリーン座標にいる敵を取得"""
        # スクリーン座標をワールド座標に変換
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y
        
        # 各Cityにいるキャラクターを収集
        character_positions = self.get_character_positions_by_city()
        
        for enemy in self.enemies:
            # キャラクターの描画位置を計算（重なり防止と同じロジック）
            if enemy.current_city and not enemy.is_moving:
                # 移動中でない場合のみオフセットを適用
                city_characters = character_positions[enemy.current_city]
                char_index = next((idx for idx, (char_type, char) in enumerate(city_characters) 
                                 if char_type == 'enemy' and char == enemy), 0)
                
                offset_x = 0
                if len(city_characters) > 1:
                    total_width = len(city_characters) * enemy.width
                    start_x = -(total_width - enemy.width) // 2
                    offset_x = start_x + char_index * enemy.width
                
                adjusted_x = enemy.x + offset_x
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
        # Qキーでタイトルシーンに戻る
        if pyxel.btnp(pyxel.KEY_Q):
            from game import TitleScene
            return TitleScene()
        
        # ESCキーでプレイヤー選択を解除
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            if self.current_turn == "player":
                self.selected_player = None
            else:
                self.selected_enemy = None
            
        # Vキーでデバッグ情報の表示切り替え
        if pyxel.btnp(pyxel.KEY_V):
            self.show_debug_info = not self.show_debug_info
            
        # Spaceキーでターンスキップ
        if pyxel.btnp(pyxel.KEY_SPACE):
            if not any(player.is_moving for player in self.players) and \
               not any(enemy.is_moving for enemy in self.enemies):
                self.switch_turn()
        
        # 敵のAI処理（エネミーターン時）
        if self.current_turn == "enemy" and self.can_move_this_turn():
            # 敵が移動していない場合のみAIタイマーを進める
            if not any(enemy.is_moving for enemy in self.enemies):
                self.ai_timer += 1
                
                # AI決定遅延時間が経過したら敵の行動を実行
                if self.ai_timer >= self.ai_decision_delay:
                    self.execute_enemy_ai_turn()
                    self.ai_timer = 0
        
        # マウスクリック検出
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.click_x = pyxel.mouse_x
            self.click_y = pyxel.mouse_y
            self.click_timer = 120  # 4秒間表示（30fps * 4秒）
            
            if self.current_turn == "player" and self.can_move_this_turn():
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
                        self.selected_player.target_city = clicked_city
                        self.selected_player.is_moving = True
                        self.player_moved_this_turn = True
                    elif current_city and current_city != clicked_city:
                        # 接続されていないCityへの移動は拒否
                        pass
                    elif current_city == clicked_city:
                        # 同じCityをクリックした場合は移動しない
                        pass
            
            elif self.current_turn == "enemy" and self.can_move_this_turn():
                # エネミーターン：敵とCityのクリック処理
                clicked_enemy = self.get_enemy_at_position(self.click_x, self.click_y)
                clicked_city = self.get_city_at_position(self.click_x, self.click_y)
                
                if clicked_enemy:
                    # 敵を選択
                    self.selected_enemy = clicked_enemy
                elif clicked_city and self.selected_enemy:
                    # 敵の現在位置のCityを取得
                    current_city = self.selected_enemy.current_city
                    
                    if current_city and self.is_cities_connected(current_city, clicked_city):
                        # 接続されているCityにのみ移動可能
                        self.selected_enemy.target_x = clicked_city.x
                        self.selected_enemy.target_y = clicked_city.y
                        self.selected_enemy.target_city = clicked_city
                        self.selected_enemy.is_moving = True
                        self.enemy_moved_this_turn = True
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
        for player in self.players:
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
                    player.current_city = player.target_city  # 現在位置Cityを更新
                    player.is_moving = False
                    player.target_x = None
                    player.target_y = None
                    player.target_city = None
                    # プレイヤーの移動完了時にターン切り替え
                    if self.current_turn == "player":
                        self.switch_turn()
                else:
                    # 目標地点に向かって移動
                    player.x += (dx / distance) * player.speed
                    player.y += (dy / distance) * player.speed
        
        # 敵の移動処理
        for enemy in self.enemies:
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
                    enemy.current_city = enemy.target_city  # 現在位置Cityを更新
                    enemy.is_moving = False
                    enemy.target_x = None
                    enemy.target_y = None
                    enemy.target_city = None
                    # 敵の移動完了時にターン切り替え
                    if self.current_turn == "enemy":
                        self.switch_turn()
                else:
                    # 目標地点に向かって移動
                    enemy.x += (dx / distance) * enemy.speed
                    enemy.y += (dy / distance) * enemy.speed
            
        # カメラの移動（WASDキー）
        if pyxel.btn(pyxel.KEY_W):
            self.camera_y -= self.camera_speed
        if pyxel.btn(pyxel.KEY_S):
            self.camera_y += self.camera_speed
        if pyxel.btn(pyxel.KEY_A):
            self.camera_x -= self.camera_speed
        if pyxel.btn(pyxel.KEY_D):
            self.camera_x += self.camera_speed
            
        # カメラ位置をマップ範囲内に制限
        self.camera_x = max(0, min(self.camera_x, self.map_pixel_width - screen_width))
        self.camera_y = max(0, min(self.camera_y, self.map_pixel_height - screen_height))
        
        return self


    def draw(self):
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
        for road in self.roads:
            city1_screen_x = road.city1.x - self.camera_x
            city1_screen_y = road.city1.y - self.camera_y
            city2_screen_x = road.city2.x - self.camera_x
            city2_screen_y = road.city2.y - self.camera_y
            
            # 線分が画面と交差するかチェック（より正確な判定）
            if self.line_intersects_screen(city1_screen_x, city1_screen_y, city2_screen_x, city2_screen_y):
                pyxel.line(city1_screen_x, city1_screen_y, city2_screen_x, city2_screen_y, 9)  # オレンジ色の線
        
        # Cityを描画
        for city in self.cities:
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
        for i, player in enumerate(self.players):
            # キャラクターの描画位置を計算
            if player.current_city and not player.is_moving:
                # 移動中でない場合のみ同じCity内での位置調整を行う
                city_characters = character_positions[player.current_city]
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
                # 移動中または現在のCityがない場合はオフセットなし
                player_screen_x = player.x - self.camera_x
                
            player_screen_y = player.y - self.camera_y
            
            # プレイヤーが画面内にある場合のみ描画
            if (-player.width <= player_screen_x <= screen_width + player.width and
                -player.height <= player_screen_y <= screen_height + player.height):
                
                # プレイヤーキャラクター（resources.pyxresのImage0左上16x16ビットマップ）
                half_width = player.width // 2
                half_height = player.height // 2
                
                # アニメーションフレームを計算（2つのフレームを交互に表示）
                anim_frame = (pyxel.frame_count // 10) % 2
                src_x = anim_frame * 16  # 0または16
                
                # 向いている方向に応じて描画幅を調整（右向きの場合は負の値で反転）
                draw_width = player.width if not player.facing_right else -player.width
                
                pyxel.blt(
                    int(player_screen_x - half_width), 
                    int(player_screen_y - half_height), 
                    0,  # Image Bank 0
                    src_x,  # ソース画像のX座標（0または16）
                    0,  # ソース画像のY座標（左上）
                    draw_width, # 幅（負の値で左右反転）
                    player.height, # 高さ
                    0   # 透明色（黒を透明にする）
                )
                
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
        for i, enemy in enumerate(self.enemies):
            # キャラクターの描画位置を計算
            if enemy.current_city and not enemy.is_moving:
                # 移動中でない場合のみ同じCity内での位置調整を行う
                city_characters = character_positions[enemy.current_city]
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
                # 移動中または現在のCityがない場合はオフセットなし
                enemy_screen_x = enemy.x - self.camera_x
                
            enemy_screen_y = enemy.y - self.camera_y
            
            # 敵が画面内にある場合のみ描画
            if (-enemy.width <= enemy_screen_x <= screen_width + enemy.width and
                -enemy.height <= enemy_screen_y <= screen_height + enemy.height):
                
                # 敵キャラクター（resources.pyxresのImage0縦2段目16x16ビットマップ）
                half_width = enemy.width // 2
                half_height = enemy.height // 2
                
                # アニメーションフレームを計算（2つのフレームを交互に表示）
                anim_frame = (pyxel.frame_count // 10) % 2
                src_x = anim_frame * 16  # 0または16
                src_y = 16  # 縦2段目
                
                # 向いている方向に応じて描画幅を調整（右向きの場合は負の値で反転）
                draw_width = enemy.width if not enemy.facing_right else -enemy.width
                
                pyxel.blt(
                    int(enemy_screen_x - half_width), 
                    int(enemy_screen_y - half_height), 
                    0,  # Image Bank 0
                    src_x,  # ソース画像のX座標（0または16）
                    src_y,  # ソース画像のY座標（縦2段目）
                    draw_width, # 幅（負の値で左右反転）
                    enemy.height, # 高さ
                    0   # 透明色（黒を透明にする）
                )
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
                if (self.current_turn == "enemy" and self.ai_timer > 0 and 
                    enemy == self.current_ai_enemy):
                    # 点滅する思考インジケーター
                    if (pyxel.frame_count // 5) % 2 == 0:
                        pyxel.circ(int(enemy_screen_x), int(enemy_screen_y - half_height - 12), 3, 7)  # 白色の思考バブル
                
                # 選択された敵に点滅する枠線を描画（エネミーターン時）
                if enemy == self.selected_enemy and self.current_turn == "enemy":
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
        if self.show_debug_info:
            pyxel.text(5, 5, "Map Scene (30x30) - Press Q to Title", 7)
            pyxel.text(5, 15, "WASD: Move Camera, ESC: Deselect, V: Debug", 7)
            pyxel.text(5, 25, "Click: Select character, Click connected City", 7)
            
            # ターン情報を表示
            turn_text = f"Turn {self.turn_counter}: {self.current_turn.upper()} TURN"
            turn_color = 11 if self.current_turn == "player" else 8
            pyxel.text(5, 35, turn_text, turn_color)
            
            can_move = "YES" if self.can_move_this_turn() else "NO"
            move_text = f"Can move this turn: {can_move}"
            pyxel.text(5, 45, move_text, 10)
            
            # 選択中のキャラクター情報を表示
            if self.current_turn == "player" and self.selected_player:
                current_city_name = self.selected_player.current_city.name if self.selected_player.current_city else "None"
                selected_text = f"Selected Player at {current_city_name}: ({int(self.selected_player.x)}, {int(self.selected_player.y)})"
                pyxel.text(5, 55, selected_text, 11)
            elif self.current_turn == "enemy" and self.selected_enemy:
                current_city_name = self.selected_enemy.current_city.name if self.selected_enemy.current_city else "None"
                selected_text = f"Selected Enemy at {current_city_name}: ({int(self.selected_enemy.x)}, {int(self.selected_enemy.y)})"
                pyxel.text(5, 55, selected_text, 8)
            else:
                pyxel.text(5, 55, "No character selected", 8)
            
            # カメラ位置を表示
            camera_text = f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})"
            pyxel.text(5, 65, camera_text, 10)
            # Cities情報を表示
            pyxel.text(5, 85, "Cities:", 14)
            for i, city in enumerate(self.cities):
                city_info = f"{city.name}: ({int(city.x)}, {int(city.y)})"
                pyxel.text(5, 95 + i * 8, city_info, 12)
            
            # 敵の情報を表示
            pyxel.text(5, 127, "Enemies:", 14)
            for i, enemy in enumerate(self.enemies):
                enemy_city_name = enemy.current_city.name if enemy.current_city else "None"
                enemy_info = f"Enemy {i+1} ({enemy.ai_type}) at {enemy_city_name}: ({int(enemy.x)}, {int(enemy.y)})"
                pyxel.text(5, 137 + i * 8, enemy_info, 8)
            
            # AI凡例を表示
            pyxel.text(5, 155, "AI Legend:", 14)
            pyxel.circ(15, 163, 2, 8)   # 赤色
            pyxel.text(20, 161, "Aggressive", 7)
            pyxel.circ(80, 163, 2, 11)  # ライトブルー  
            pyxel.text(85, 161, "Patrol", 7)
            pyxel.circ(15, 171, 2, 3)   # 緑色
            pyxel.text(20, 169, "Defensive", 7)
            pyxel.circ(80, 171, 2, 14)  # ピンク
            pyxel.text(85, 169, "Random", 7)
            
            # AI情報を表示（エネミーターン時）
            if self.current_turn == "enemy":
                ai_info = f"AI Timer: {self.ai_timer}/{self.ai_decision_delay}"
                pyxel.text(5, 181, ai_info, 8)
            
            # マウスクリック座標を表示
            if self.click_timer > 0:
                coord_text = f"Click: ({self.click_x}, {self.click_y})"
                y_pos = 191 if self.current_turn == "enemy" else 181
                pyxel.text(5, y_pos, coord_text, 8)
                
            # 現在のマウス座標も表示
            mouse_text = f"Mouse: ({pyxel.mouse_x}, {pyxel.mouse_y})"
            y_pos = 201 if self.current_turn == "enemy" else 191
            pyxel.text(5, y_pos, mouse_text, 10)
        else:
            # デバッグ情報非表示時は最小限の情報のみ
            pyxel.text(5, 5, "Press V for debug info", 8)
