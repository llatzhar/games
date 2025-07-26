import json
import os
from typing import List, Dict, Any, Optional

class City:
    def __init__(self, id: int, name: str, x: float, y: float):
        self.id = id  # 都市の一意なID
        self.name = name
        self.x = x
        self.y = y
        self.size = 20
    
    def get_hover_info(self) -> List[str]:
        """ホバー時に表示する情報を取得"""
        return [
            f"City: {self.name}",
            f"Position: ({int(self.x)}, {int(self.y)})",
            f"Size: {self.size}"
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'size': self.size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'City':
        city = cls(data['id'], data['name'], data['x'], data['y'])
        city.size = data.get('size', 20)
        return city

class Road:
    def __init__(self, city1_id: int, city2_id: int):
        self.city1_id = city1_id
        self.city2_id = city2_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'city1_id': self.city1_id,
            'city2_id': self.city2_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Road':
        return cls(data['city1_id'], data['city2_id'])

class Character:
    def __init__(self, x: float, y: float, current_city_id: Optional[int] = None, speed: float = 1, life: int = 100, attack: int = 20, image_index: int = 0):
        self.x = x
        self.y = y
        self.width = 16  # char_width相当
        self.height = 16  # char_height相当
        self.speed = speed
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None
        self.target_city_id: Optional[int] = None
        self.is_moving = False
        self.facing_right = True
        self.current_city_id = current_city_id  # 都市IDに変更
        self.image_index = image_index  # 画像の段数（0=1段目、1=2段目、2=3段目）
        # 戦闘ステータス
        self.life = life  # 残兵力（0になると消滅）
        self.max_life = life  # 最大兵力
        self.attack = attack  # 攻撃力
    
    def get_hover_info(self) -> List[str]:
        """ホバー時に表示する情報を取得（基底クラスの実装）"""
        info_lines = []
        current_city = self.current_city_id if self.current_city_id else "None"
        info_lines.append(f"Location: {current_city}")
        info_lines.append(f"Life: {self.life}/{self.max_life}")
        info_lines.append(f"Attack: {self.attack}")
        
        if self.is_moving:
            info_lines.append("Moving...")
        
        return info_lines
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'speed': self.speed,
            'target_x': self.target_x,
            'target_y': self.target_y,
            'target_city_id': self.target_city_id,
            'is_moving': self.is_moving,
            'facing_right': self.facing_right,
            'current_city_id': self.current_city_id,
            'life': self.life,
            'max_life': self.max_life,
            'attack': self.attack,
            'image_index': self.image_index
        }
    
    def update_from_dict(self, data: Dict[str, Any]):
        """辞書からキャラクターデータを更新"""
        self.x = data['x']
        self.y = data['y']
        self.width = data.get('width', 16)
        self.height = data.get('height', 16)
        self.speed = data['speed']
        self.target_x = data.get('target_x')
        self.target_y = data.get('target_y')
        self.target_city_id = data.get('target_city_id')
        self.is_moving = data.get('is_moving', False)
        self.facing_right = data.get('facing_right', True)
        self.current_city_id = data.get('current_city_id')
        self.life = data.get('life', 100)
        self.max_life = data.get('max_life', 100)
        self.attack = data.get('attack', 20)
        self.image_index = data.get('image_index', 0)

class Player(Character):
    def __init__(self, x: float, y: float, current_city_id: Optional[int] = None):
        super().__init__(x, y, current_city_id, speed=2, life=120, attack=25, image_index=0)  # 1段目を使用
    
    def get_hover_info(self) -> List[str]:
        """プレイヤー用のホバー情報を取得"""
        info_lines = ["Player"]
        info_lines.extend(super().get_hover_info())
        return info_lines
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['type'] = 'player'
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        player = cls(data['x'], data['y'], data.get('current_city_id'))
        player.update_from_dict(data)
        return player

class Enemy(Character):
    def __init__(self, x: float, y: float, current_city_id: Optional[int] = None, ai_type: str = "random", image_index: int = 1):
        super().__init__(x, y, current_city_id, speed=1, life=80, attack=20, image_index=image_index)  # 2段目以降を使用
        self.ai_type = ai_type
        self.patrol_city_ids: List[int] = []  # 都市IDのリストに変更
        self.patrol_index = 0
        self.last_player_position: Optional[Dict[str, float]] = None
    
    def get_hover_info(self) -> List[str]:
        """敵用のホバー情報を取得"""
        info_lines = [f"Enemy ({self.ai_type})"]
        info_lines.extend(super().get_hover_info())
        
        # AI特性の説明を追加
        if self.ai_type == "aggressive":
            info_lines.append("Pursues players")
        elif self.ai_type == "defensive":
            info_lines.append("Avoids players")
        elif self.ai_type == "patrol":
            info_lines.append("Patrols route")
        elif self.ai_type == "random":
            info_lines.append("Moves randomly")
        
        return info_lines
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'type': 'enemy',
            'ai_type': self.ai_type,
            'patrol_city_ids': self.patrol_city_ids,
            'patrol_index': self.patrol_index,
            'last_player_position': self.last_player_position
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Enemy':
        image_index = data.get('image_index', 1)  # デフォルトで2段目を使用
        enemy = cls(data['x'], data['y'], data.get('current_city_id'), data.get('ai_type', 'random'), image_index)
        enemy.update_from_dict(data)
        enemy.patrol_city_ids = data.get('patrol_city_ids', [])
        enemy.patrol_index = data.get('patrol_index', 0)
        enemy.last_player_position = data.get('last_player_position')
        return enemy

class GameState:
    def __init__(self):
        self.cities: Dict[int, City] = {}  # 整数IDをキーに変更
        self.roads: List[Road] = []
        self.players: List[Player] = []
        self.enemies: List[Enemy] = []
        self.current_turn = "player"
        self.turn_counter = 1
        self.player_moved_this_turn = False
        self.enemy_moved_this_turn = False
        self.ai_timer = 0
        self.ai_decision_delay = 60
        self.current_ai_enemy_index: Optional[int] = None
        
        # ゲーム状態ファイルのパス
        self.save_file_path = os.path.join("saves", "game_state.json")
        
        # savesフォルダが存在しない場合は作成
        os.makedirs(os.path.dirname(self.save_file_path), exist_ok=True)
    
    def initialize_default_state(self):
        """デフォルトのゲーム状態を初期化"""
        tile_size = 16
        
        # 都市を作成（整数IDを使用）
        self.cities = {
            1: City(1, "Kiyosu", 2 * tile_size, 2 * tile_size),
            2: City(2, "Nagoya", 7 * tile_size, 2 * tile_size),
            3: City(3, "Sakai", 2 * tile_size, 6 * tile_size),
            4: City(4, "Yamato", 7 * tile_size, 6 * tile_size),
            5: City(5, "Tutujigaoka", 12 * tile_size, 2 * tile_size),
            6: City(6, "Iwabuti", 12 * tile_size, 6 * tile_size),
        }
        
        # 道路を作成（都市IDを使用）
        self.roads = [
            Road(1, 2),  # Kiyosu - Nagoya
            Road(2, 5),  # Nagoya - Tutujigaoka
            Road(1, 3),  # Kiyosu - Sakai
            Road(3, 4),  # Sakai - Yamato
            Road(4, 6),  # Yamato - Iwabuti
            Road(2, 4),  # Nagoya - Yamato
            Road(5, 6),  # Tutujigaoka - Iwabuti
            Road(1, 4),  # Kiyosu - Yamato
            Road(2, 6),  # Nagoya - Iwabuti
        ]
        
        # プレイヤーを作成
        self.players = [
            Player(self.cities[1].x, self.cities[1].y, 1),  # Kiyosu
            Player(self.cities[3].x, self.cities[3].y, 3),  # Sakai
        ]
        # 敵を作成
        enemy1 = Enemy(self.cities[5].x, self.cities[5].y, 5, "aggressive", 1)  # Tutujigaoka
        enemy2 = Enemy(self.cities[6].x, self.cities[6].y, 6, "patrol", 2)     # Iwabuti
        enemy2.patrol_city_ids = [6, 4, 2, 5]  # Iwabuti - Yamato - Nagoya - Tutujigaoka
        
        self.enemies = [enemy1, enemy2]
    
    def get_city_by_id(self, city_id: int) -> Optional[City]:
        """IDで都市を取得"""
        return self.cities.get(city_id)
    
    def get_city_display_name(self, city_id: int) -> str:
        """都市IDから表示名を取得"""
        city = self.cities.get(city_id)
        return city.name if city else str(city_id)
    
    def get_connected_city_ids(self, city_id: int) -> List[int]:
        """指定した都市に接続されている都市IDのリストを取得"""
        connected = []
        for road in self.roads:
            if road.city1_id == city_id:
                connected.append(road.city2_id)
            elif road.city2_id == city_id:
                connected.append(road.city1_id)
        return connected
    
    def are_cities_connected(self, city1_id: int, city2_id: int) -> bool:
        """2つの都市が道路で接続されているかチェック"""
        for road in self.roads:
            if (road.city1_id == city1_id and road.city2_id == city2_id) or \
               (road.city1_id == city2_id and road.city2_id == city1_id):
                return True
        return False
    
    def switch_turn(self):
        """ターンを切り替える"""
        if self.current_turn == "player":
            self.current_turn = "enemy"
            self.player_moved_this_turn = False
            self.ai_timer = 0
        else:
            self.current_turn = "player"
            self.enemy_moved_this_turn = False
            self.turn_counter += 1
            self.ai_timer = 0
    
    def can_move_this_turn(self) -> bool:
        """このターンで移動可能かチェック"""
        if self.current_turn == "player":
            return not self.player_moved_this_turn
        else:
            return not self.enemy_moved_this_turn
    
    def to_dict(self) -> Dict[str, Any]:
        """ゲーム状態を辞書に変換"""
        return {
            'cities': {str(city_id): city.to_dict() for city_id, city in self.cities.items()},
            'roads': [road.to_dict() for road in self.roads],
            'players': [player.to_dict() for player in self.players],
            'enemies': [enemy.to_dict() for enemy in self.enemies],
            'current_turn': self.current_turn,
            'turn_counter': self.turn_counter,
            'player_moved_this_turn': self.player_moved_this_turn,
            'enemy_moved_this_turn': self.enemy_moved_this_turn,
            'ai_timer': self.ai_timer,
            'ai_decision_delay': self.ai_decision_delay,
            'current_ai_enemy_index': self.current_ai_enemy_index
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """辞書からゲーム状態を復元"""
        # 都市を復元
        self.cities = {int(city_id): City.from_dict(city_data) 
                      for city_id, city_data in data['cities'].items()}
        
        # 道路を復元
        self.roads = [Road.from_dict(road_data) for road_data in data['roads']]
        
        # プレイヤーを復元
        self.players = [Player.from_dict(player_data) for player_data in data['players']]
        
        # 敵を復元
        self.enemies = [Enemy.from_dict(enemy_data) for enemy_data in data['enemies']]
        
        # その他の状態を復元
        self.current_turn = data['current_turn']
        self.turn_counter = data['turn_counter']
        self.player_moved_this_turn = data['player_moved_this_turn']
        self.enemy_moved_this_turn = data['enemy_moved_this_turn']
        self.ai_timer = data.get('ai_timer', 0)
        self.ai_decision_delay = data.get('ai_decision_delay', 60)
        self.current_ai_enemy_index = data.get('current_ai_enemy_index')
    
    def save_to_file(self):
        """ゲーム状態をJSONファイルに保存"""
        try:
            with open(self.save_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"Game state saved to {self.save_file_path}")
        except Exception as e:
            print(f"Failed to save game state: {e}")
    
    def load_from_file(self) -> bool:
        """JSONファイルからゲーム状態をロード"""
        try:
            if os.path.exists(self.save_file_path):
                with open(self.save_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.from_dict(data)
                print(f"Game state loaded from {self.save_file_path}")
                return True
            else:
                print(f"Save file not found: {self.save_file_path}")
                return False
        except Exception as e:
            print(f"Failed to load game state: {e}")
            return False
    
    def check_battles(self):
        """各都市で戦闘をチェックし、戦闘が発生する都市の情報を返す（実際の戦闘は実行しない）"""
        battle_locations = []
        
        for city_id, city in self.cities.items():
            # この都市にいるプレイヤーと敵を取得
            players_in_city = [p for p in self.players if p.current_city_id == city_id and not p.is_moving]
            enemies_in_city = [e for e in self.enemies if e.current_city_id == city_id and not e.is_moving]
            
            # プレイヤーと敵の両方がいる場合は戦闘
            if players_in_city and enemies_in_city:
                battle_info = {
                    'city_id': city_id,
                    'players': players_in_city.copy(),  # コピーして元のリストを保護
                    'enemies': enemies_in_city.copy(),
                    'players_before': len(players_in_city),
                    'enemies_before': len(enemies_in_city)
                }
                battle_locations.append(battle_info)
        
        return battle_locations

    def check_and_execute_battles(self):
        """各都市で戦闘をチェックし実行する（キャラクター削除は別途実行）"""
        battle_results = []
        
        for city_id, city in self.cities.items():
            # この都市にいるプレイヤーと敵を取得
            players_in_city = [p for p in self.players if p.current_city_id == city_id and not p.is_moving]
            enemies_in_city = [e for e in self.enemies if e.current_city_id == city_id and not e.is_moving]
            
            # プレイヤーと敵の両方がいる場合は戦闘
            if players_in_city and enemies_in_city:
                battle_result = self.execute_battle(city_id, players_in_city, enemies_in_city)
                if battle_result:
                    battle_results.append(battle_result)
        
        # 戦闘で倒されたキャラクターの削除は戦闘シーン再生後に実行
        # self.remove_defeated_characters()  # この行をコメントアウト
        
        return battle_results
    
    def execute_battle(self, city_id: int, players: List[Player], enemies: List[Enemy]) -> Dict[str, Any]:
        """指定した都市での戦闘を実行"""
        battle_log = []
        city_name = self.get_city_display_name(city_id)
        
        # プレイヤーの攻撃フェーズ
        total_player_attack = sum(p.attack for p in players)
        if enemies:
            # 最も弱い敵から攻撃
            target_enemy = min(enemies, key=lambda e: e.life)
            damage = min(total_player_attack, target_enemy.life)
            target_enemy.life -= damage
            battle_log.append(f"Players dealt {damage} damage to {target_enemy.ai_type} enemy in {city_name}")
        
        # 敵の攻撃フェーズ
        total_enemy_attack = sum(e.attack for e in enemies)
        if players:
            # 最も弱いプレイヤーから攻撃
            target_player = min(players, key=lambda p: p.life)
            damage = min(total_enemy_attack, target_player.life)
            target_player.life -= damage
            battle_log.append(f"Enemies dealt {damage} damage to player in {city_name}")
        
        return {
            'city_id': city_id,
            'log': battle_log,
            'players_before': len(players),
            'enemies_before': len(enemies)
        }
    
    def remove_defeated_characters(self):
        """lifeが0以下のキャラクターを削除"""
        # プレイヤーから削除
        original_player_count = len(self.players)
        self.players = [p for p in self.players if p.life > 0]
        players_defeated = original_player_count - len(self.players)
        
        # 敵から削除
        original_enemy_count = len(self.enemies)
        self.enemies = [e for e in self.enemies if e.life > 0]
        enemies_defeated = original_enemy_count - len(self.enemies)
        
        if players_defeated > 0:
            print(f"{players_defeated} player(s) were defeated!")
        if enemies_defeated > 0:
            print(f"{enemies_defeated} enemy(ies) were defeated!")
    
    def get_characters_in_city(self, city_id: int) -> tuple[List[Player], List[Enemy]]:
        """指定した都市にいるキャラクターを取得"""
        players_in_city = [p for p in self.players if p.current_city_id == city_id and not p.is_moving]
        enemies_in_city = [e for e in self.enemies if e.current_city_id == city_id and not e.is_moving]
        return players_in_city, enemies_in_city

    def auto_save(self):
        """自動セーブを実行"""
        self.save_to_file()
