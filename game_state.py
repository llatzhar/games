import json
import os
from typing import List, Dict, Any, Optional

class City:
    def __init__(self, name: str, x: float, y: float):
        self.name = name
        self.x = x
        self.y = y
        self.size = 20
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'size': self.size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'City':
        city = cls(data['name'], data['x'], data['y'])
        city.size = data.get('size', 20)
        return city

class Road:
    def __init__(self, city1_name: str, city2_name: str):
        self.city1_name = city1_name
        self.city2_name = city2_name
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'city1_name': self.city1_name,
            'city2_name': self.city2_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Road':
        return cls(data['city1_name'], data['city2_name'])

class Character:
    def __init__(self, x: float, y: float, current_city_name: Optional[str] = None, speed: float = 1):
        self.x = x
        self.y = y
        self.width = 16  # char_width相当
        self.height = 16  # char_height相当
        self.speed = speed
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None
        self.target_city_name: Optional[str] = None
        self.is_moving = False
        self.facing_right = True
        self.current_city_name = current_city_name
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'speed': self.speed,
            'target_x': self.target_x,
            'target_y': self.target_y,
            'target_city_name': self.target_city_name,
            'is_moving': self.is_moving,
            'facing_right': self.facing_right,
            'current_city_name': self.current_city_name
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
        self.target_city_name = data.get('target_city_name')
        self.is_moving = data.get('is_moving', False)
        self.facing_right = data.get('facing_right', True)
        self.current_city_name = data.get('current_city_name')

class Player(Character):
    def __init__(self, x: float, y: float, current_city_name: Optional[str] = None):
        super().__init__(x, y, current_city_name, speed=2)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['type'] = 'player'
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        player = cls(data['x'], data['y'], data.get('current_city_name'))
        player.update_from_dict(data)
        return player

class Enemy(Character):
    def __init__(self, x: float, y: float, current_city_name: Optional[str] = None, ai_type: str = "random"):
        super().__init__(x, y, current_city_name, speed=1)
        self.ai_type = ai_type
        self.patrol_city_names: List[str] = []
        self.patrol_index = 0
        self.last_player_position: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'type': 'enemy',
            'ai_type': self.ai_type,
            'patrol_city_names': self.patrol_city_names,
            'patrol_index': self.patrol_index,
            'last_player_position': self.last_player_position
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Enemy':
        enemy = cls(data['x'], data['y'], data.get('current_city_name'), data.get('ai_type', 'random'))
        enemy.update_from_dict(data)
        enemy.patrol_city_names = data.get('patrol_city_names', [])
        enemy.patrol_index = data.get('patrol_index', 0)
        enemy.last_player_position = data.get('last_player_position')
        return enemy

class GameState:
    def __init__(self):
        self.cities: Dict[str, City] = {}
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
        
        # 都市を作成
        self.cities = {
            "Town A": City("Town A", 2 * tile_size, 2 * tile_size),
            "Town B": City("Town B", 7 * tile_size, 2 * tile_size),
            "Town C": City("Town C", 2 * tile_size, 6 * tile_size),
            "Town D": City("Town D", 7 * tile_size, 6 * tile_size),
            "Town E": City("Town E", 12 * tile_size, 2 * tile_size),
            "Town F": City("Town F", 12 * tile_size, 6 * tile_size),
        }
        
        # 道路を作成
        self.roads = [
            Road("Town A", "Town B"),
            Road("Town B", "Town E"),
            Road("Town A", "Town C"),
            Road("Town C", "Town D"),
            Road("Town D", "Town F"),
            Road("Town B", "Town D"),
            Road("Town E", "Town F"),
            Road("Town A", "Town D"),
            Road("Town B", "Town F"),
        ]
        
        # プレイヤーを作成
        self.players = [
            Player(self.cities["Town A"].x, self.cities["Town A"].y, "Town A"),
            Player(self.cities["Town C"].x, self.cities["Town C"].y, "Town C"),
        ]
        
        # 敵を作成
        enemy1 = Enemy(self.cities["Town E"].x, self.cities["Town E"].y, "Town E", "aggressive")
        enemy2 = Enemy(self.cities["Town F"].x, self.cities["Town F"].y, "Town F", "patrol")
        enemy2.patrol_city_names = ["Town F", "Town D", "Town B", "Town E"]
        
        self.enemies = [enemy1, enemy2]
    
    def get_city_by_name(self, name: str) -> Optional[City]:
        """名前で都市を取得"""
        return self.cities.get(name)
    
    def get_connected_city_names(self, city_name: str) -> List[str]:
        """指定した都市に接続されている都市名のリストを取得"""
        connected = []
        for road in self.roads:
            if road.city1_name == city_name:
                connected.append(road.city2_name)
            elif road.city2_name == city_name:
                connected.append(road.city1_name)
        return connected
    
    def are_cities_connected(self, city1_name: str, city2_name: str) -> bool:
        """2つの都市が道路で接続されているかチェック"""
        for road in self.roads:
            if (road.city1_name == city1_name and road.city2_name == city2_name) or \
               (road.city1_name == city2_name and road.city2_name == city1_name):
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
            'cities': {name: city.to_dict() for name, city in self.cities.items()},
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
        self.cities = {name: City.from_dict(city_data) 
                      for name, city_data in data['cities'].items()}
        
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
    
    def auto_save(self):
        """自動セーブを実行"""
        self.save_to_file()
