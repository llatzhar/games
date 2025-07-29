import json
import os
from typing import Any, Dict, List, Optional

from coordinate_utils import create_default_coordinate_transformer


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
            f"Size: {self.size}",
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "City":
        city = cls(data["id"], data["name"], data["x"], data["y"])
        city.size = data.get("size", 20)
        return city


class Road:
    def __init__(self, city1_id: int, city2_id: int):
        self.city1_id = city1_id
        self.city2_id = city2_id

    def to_dict(self) -> Dict[str, Any]:
        return {"city1_id": self.city1_id, "city2_id": self.city2_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Road":
        return cls(data["city1_id"], data["city2_id"])


class Character:
    def __init__(
        self,
        x: float,
        y: float,
        current_city_id: Optional[int] = None,
        speed: float = 1,
        life: int = 100,
        attack: int = 20,
        initiative: int = 10,
        image_index: int = 0,
    ):
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
        self.initiative = initiative  # イニシアチブ値（行動順決定）

    def get_hover_info(self) -> List[str]:
        """ホバー時に表示する情報を取得（基底クラスの実装）"""
        info_lines = []
        current_city = self.current_city_id if self.current_city_id else "None"
        info_lines.append(f"Location: {current_city}")
        info_lines.append(f"Life: {self.life}/{self.max_life}")
        info_lines.append(f"Attack: {self.attack}")
        info_lines.append(f"Initiative: {self.initiative}")

        if self.is_moving:
            info_lines.append("Moving...")

        return info_lines

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "speed": self.speed,
            "target_x": self.target_x,
            "target_y": self.target_y,
            "target_city_id": self.target_city_id,
            "is_moving": self.is_moving,
            "facing_right": self.facing_right,
            "current_city_id": self.current_city_id,
            "life": self.life,
            "max_life": self.max_life,
            "attack": self.attack,
            "initiative": self.initiative,
            "image_index": self.image_index,
        }

    def update_from_dict(self, data: Dict[str, Any]):
        """辞書からキャラクターデータを更新"""
        self.x = data["x"]
        self.y = data["y"]
        self.width = data.get("width", 16)
        self.height = data.get("height", 16)
        self.speed = data["speed"]
        self.target_x = data.get("target_x")
        self.target_y = data.get("target_y")
        self.target_city_id = data.get("target_city_id")
        self.is_moving = data.get("is_moving", False)
        self.facing_right = data.get("facing_right", True)
        self.current_city_id = data.get("current_city_id")
        self.life = data.get("life", 100)
        self.max_life = data.get("max_life", 100)
        self.attack = data.get("attack", 20)
        self.initiative = data.get("initiative", 10)
        self.image_index = data.get("image_index", 0)


class Player(Character):
    def __init__(
        self,
        x: float,
        y: float,
        current_city_id: Optional[int] = None,
        initiative: int = 15,
    ):
        super().__init__(
            x,
            y,
            current_city_id,
            speed=2,
            life=120,
            attack=25,
            initiative=initiative,
            image_index=0,
        )  # 1段目を使用、イニシアチブを引数で受け取る

    def get_hover_info(self) -> List[str]:
        """プレイヤー用のホバー情報を取得"""
        info_lines = ["Player"]
        info_lines.extend(super().get_hover_info())
        return info_lines

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["type"] = "player"
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        initiative = data.get("initiative", 15)  # デフォルトは15
        player = cls(data["x"], data["y"], data.get("current_city_id"), initiative)
        player.update_from_dict(data)
        return player


class Enemy(Character):
    def __init__(
        self,
        x: float,
        y: float,
        current_city_id: Optional[int] = None,
        ai_type: str = "random",
        image_index: int = 1,
    ):
        # AIタイプに応じてイニシアチブを設定
        initiative_by_type = {
            "aggressive": 12,  # 積極的：やや高い
            "defensive": 8,  # 防御的：低い
            "patrol": 10,  # パトロール：標準
            "random": 10,  # ランダム：標準
        }
        initiative = initiative_by_type.get(ai_type, 10)

        super().__init__(
            x,
            y,
            current_city_id,
            speed=1,
            life=80,
            attack=20,
            initiative=initiative,
            image_index=image_index,
        )  # 2段目以降を使用
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
        data.update(
            {
                "type": "enemy",
                "ai_type": self.ai_type,
                "patrol_city_ids": self.patrol_city_ids,
                "patrol_index": self.patrol_index,
                "last_player_position": self.last_player_position,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Enemy":
        image_index = data.get("image_index", 1)  # デフォルトで2段目を使用
        enemy = cls(
            data["x"],
            data["y"],
            data.get("current_city_id"),
            data.get("ai_type", "random"),
            image_index,
        )
        enemy.update_from_dict(data)
        enemy.patrol_city_ids = data.get("patrol_city_ids", [])
        enemy.patrol_index = data.get("patrol_index", 0)
        enemy.last_player_position = data.get("last_player_position")
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
        """デフォルトのゲーム状態を初期化（中央座標系）"""
        # 座標変換器を使用
        coord_transformer = create_default_coordinate_transformer()

        # 都市を作成（中央座標系を使用）
        self.cities = {
            1: City(
                1, "Central", *coord_transformer.tile_to_pixel(0, 0)
            ),  # タイル(0,0) → 物理座標(256,256)
            2: City(
                2, "West", *coord_transformer.tile_to_pixel(-1, 2)
            ),  # タイル(-1,2) → 物理座標(224,320)
            3: City(
                3, "East", *coord_transformer.tile_to_pixel(1, 2)
            ),  # タイル(1,2) → 物理座標(288,320)
            4: City(
                4, "North", *coord_transformer.tile_to_pixel(0, -2)
            ),  # タイル(0,-2) → 物理座標(256,192)
            5: City(
                5, "South", *coord_transformer.tile_to_pixel(0, 3)
            ),  # タイル(0,3) → 物理座標(256,352)
            6: City(
                6, "Northeast", *coord_transformer.tile_to_pixel(2, -1)
            ),  # タイル(2,-1) → 物理座標(320,224)
        }

        # 道路を作成（都市IDを使用）
        self.roads = [
            Road(1, 2),  # Central - West
            Road(1, 3),  # Central - East
            Road(2, 3),  # West - East
            Road(1, 4),  # Central - North
            Road(1, 5),  # Central - South
            Road(2, 5),  # West - South
            Road(3, 5),  # East - South
            Road(3, 6),  # East - Northeast
            Road(4, 6),  # North - Northeast
        ]

        # プレイヤーを作成（タイル(0,0)とタイル(-1,2)に配置）
        self.players = [
            Player(self.cities[1].x, self.cities[1].y, 1),  # Central (0,0)
            Player(self.cities[2].x, self.cities[2].y, 2, initiative=10),  # West (-1,2)
        ]

        # 敵を作成（タイル(1,2)に1体配置）
        enemy1 = Enemy(
            self.cities[3].x, self.cities[3].y, 3, "aggressive", 1
        )  # East (1,2)

        self.enemies = [enemy1]

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
            if (road.city1_id == city1_id and road.city2_id == city2_id) or (
                road.city1_id == city2_id and road.city2_id == city1_id
            ):
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
            "cities": {
                str(city_id): city.to_dict() for city_id, city in self.cities.items()
            },
            "roads": [road.to_dict() for road in self.roads],
            "players": [player.to_dict() for player in self.players],
            "enemies": [enemy.to_dict() for enemy in self.enemies],
            "current_turn": self.current_turn,
            "turn_counter": self.turn_counter,
            "player_moved_this_turn": self.player_moved_this_turn,
            "enemy_moved_this_turn": self.enemy_moved_this_turn,
            "ai_timer": self.ai_timer,
            "ai_decision_delay": self.ai_decision_delay,
            "current_ai_enemy_index": self.current_ai_enemy_index,
        }

    def from_dict(self, data: Dict[str, Any]):
        """辞書からゲーム状態を復元"""
        # 都市を復元
        self.cities = {
            int(city_id): City.from_dict(city_data)
            for city_id, city_data in data["cities"].items()
        }

        # 道路を復元
        self.roads = [Road.from_dict(road_data) for road_data in data["roads"]]

        # プレイヤーを復元
        self.players = [
            Player.from_dict(player_data) for player_data in data["players"]
        ]

        # 敵を復元
        self.enemies = [Enemy.from_dict(enemy_data) for enemy_data in data["enemies"]]

        # その他の状態を復元
        self.current_turn = data["current_turn"]
        self.turn_counter = data["turn_counter"]
        self.player_moved_this_turn = data["player_moved_this_turn"]
        self.enemy_moved_this_turn = data["enemy_moved_this_turn"]
        self.ai_timer = data.get("ai_timer", 0)
        self.ai_decision_delay = data.get("ai_decision_delay", 60)
        self.current_ai_enemy_index = data.get("current_ai_enemy_index")

    def save_to_file(self):
        """ゲーム状態をJSONファイルに保存"""
        try:
            with open(self.save_file_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"Game state saved to {self.save_file_path}")
        except Exception as e:
            print(f"Failed to save game state: {e}")

    def load_from_file(self) -> bool:
        """JSONファイルからゲーム状態をロード"""
        try:
            if os.path.exists(self.save_file_path):
                with open(self.save_file_path, "r", encoding="utf-8") as f:
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
            players_in_city = [
                p
                for p in self.players
                if p.current_city_id == city_id and not p.is_moving
            ]
            enemies_in_city = [
                e
                for e in self.enemies
                if e.current_city_id == city_id and not e.is_moving
            ]

            # プレイヤーと敵の両方がいる場合は戦闘
            if players_in_city and enemies_in_city:
                battle_info = {
                    "city_id": city_id,
                    "players": players_in_city.copy(),  # コピーして元のリストを保護
                    "enemies": enemies_in_city.copy(),
                    "players_before": len(players_in_city),
                    "enemies_before": len(enemies_in_city),
                }
                battle_locations.append(battle_info)

        return battle_locations

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
        players_in_city = [
            p for p in self.players if p.current_city_id == city_id and not p.is_moving
        ]
        enemies_in_city = [
            e for e in self.enemies if e.current_city_id == city_id and not e.is_moving
        ]
        return players_in_city, enemies_in_city

    def auto_save(self):
        """自動セーブを実行"""
        self.save_to_file()
