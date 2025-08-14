import json
import os
import random
from typing import Any, Dict, List, Optional

from coordinate_utils import create_default_coordinate_transformer
from geometry_utils import point_too_close_to_line, roads_intersect

# 都市発見の設定
CITY_DISCOVERY_INTERVAL = 1  # nターンごとに新都市発見（n=1で毎ターン）

# 都市とキャラクターの名前組み合わせ辞書
CITY_CHARACTER_NAMES = {
    "Central": {
        "players": ["Arthur", "Elena", "Marcus", "Sophia"],
        "enemies": ["Shadow", "Raven", "Viper", "Frost"]
    },
    "West": {
        "players": ["Gareth", "Luna", "Victor", "Rose"],
        "enemies": ["Iron", "Storm", "Blade", "Mist"]
    },
    "East": {
        "players": ["Kai", "Nova", "Rex", "Pearl"],
        "enemies": ["Fang", "Ghost", "Thorn", "Ash"]
    },
    "Forest": {
        "players": ["Robin", "Sage", "Cedar", "Ivy"],
        "enemies": ["Wolf", "Bear", "Hawk", "Fox"]
    },
    "Mountain": {
        "players": ["Stone", "Peak", "Ridge", "Crystal"],
        "enemies": ["Golem", "Titan", "Boulder", "Cliff"]
    },
    "Valley": {
        "players": ["River", "Brook", "Dale", "Meadow"],
        "enemies": ["Serpent", "Basilisk", "Venom", "Coil"]
    },
    "Plains": {
        "players": ["Swift", "Gale", "Field", "Grass"],
        "enemies": ["Nomad", "Rider", "Wind", "Dust"]
    },
    "Harbor": {
        "players": ["Wave", "Tide", "Marina", "Coral"],
        "enemies": ["Kraken", "Shark", "Reef", "Storm"]
    },
    "Desert": {
        "players": ["Dune", "Oasis", "Sand", "Mirage"],
        "enemies": ["Scorpion", "Viper", "Jackal", "Vulture"]
    },
    "Hill": {
        "players": ["Slope", "Crest", "Mound", "Knoll"],
        "enemies": ["Troll", "Ogre", "Giant", "Brute"]
    },
    "Lake": {
        "players": ["Azure", "Deep", "Clear", "Pure"],
        "enemies": ["Leviathan", "Hydra", "Depths", "Current"]
    },
    "River": {
        "players": ["Flow", "Current", "Stream", "Rapids"],
        "enemies": ["Pike", "Eel", "Catfish", "Trout"]
    },
    "Bridge": {
        "players": ["Span", "Arch", "Cross", "Link"],
        "enemies": ["Guardian", "Keeper", "Warden", "Sentry"]
    },
    "Canyon": {
        "players": ["Echo", "Gorge", "Cliff", "Ravine"],
        "enemies": ["Stalker", "Lurker", "Hunter", "Predator"]
    },
    "Gateway": {
        "players": ["Portal", "Pass", "Entry", "Door"],
        "enemies": ["Gatekeeper", "Sentinel", "Watch", "Guard"]
    },
    "Junction": {
        "players": ["Meet", "Cross", "Join", "Unite"],
        "enemies": ["Crossroads", "Intersection", "Node", "Hub"]
    },
    "Crossing": {
        "players": ["Path", "Way", "Route", "Trail"],
        "enemies": ["Bandit", "Raider", "Thief", "Outlaw"]
    },
    "Midway": {
        "players": ["Center", "Middle", "Half", "Balance"],
        "enemies": ["Neutral", "Void", "Empty", "Lost"]
    }
}


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
        name: str = "Unknown",
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
        self.name = name  # キャラクター名
        # 戦闘ステータス
        self.life = life  # 残兵力（0になると消滅）
        self.max_life = life  # 最大兵力
        self.attack = attack  # 攻撃力
        self.initiative = initiative  # イニシアチブ値（行動順決定）

    def get_hover_info(self) -> List[str]:
        """ホバー時に表示する情報を取得（基底クラスの実装）"""
        info_lines = []
        info_lines.append(f"Name: {self.name}")
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
            "name": self.name,
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
        self.name = data.get("name", "Unknown")


class Player(Character):
    def __init__(
        self,
        x: float,
        y: float,
        current_city_id: Optional[int] = None,
        initiative: int = 15,
        name: str = "Player",
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
            name=name,
        )  # 1段目を使用、イニシアチブを引数で受け取る

    def get_hover_info(self) -> List[str]:
        """プレイヤー用のホバー情報を取得"""
        info_lines = [f"Player: {self.name}"]
        info_lines.extend(super().get_hover_info()[1:])  # 名前以外の情報を追加
        return info_lines

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["type"] = "player"
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        initiative = data.get("initiative", 15)  # デフォルトは15
        name = data.get("name", "Player")  # デフォルトは"Player"
        player = cls(
            data["x"], data["y"], data.get("current_city_id"),
            initiative, name
        )
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
        name: str = "Enemy",
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
            name=name,
        )  # 2段目以降を使用
        self.ai_type = ai_type
        self.patrol_city_ids: List[int] = []  # 都市IDのリストに変更
        self.patrol_index = 0
        self.last_player_position: Optional[Dict[str, float]] = None

    def get_hover_info(self) -> List[str]:
        """敵用のホバー情報を取得"""
        info_lines = [f"Enemy: {self.name} ({self.ai_type})"]
        info_lines.extend(super().get_hover_info()[1:])  # 名前以外の情報を追加

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
        name = data.get("name", "Enemy")  # デフォルトは"Enemy"
        enemy = cls(
            data["x"],
            data["y"],
            data.get("current_city_id"),
            data.get("ai_type", "random"),
            image_index,
            name,
        )
        enemy.update_from_dict(data)
        enemy.patrol_city_ids = data.get("patrol_city_ids", [])
        enemy.patrol_index = data.get("patrol_index", 0)
        enemy.last_player_position = data.get("last_player_position")
        return enemy


def get_character_name_for_city(
    city_name: str, character_type: str, used_names: set = None
) -> str:
    """指定された都市とキャラクタータイプに基づいて名前を選択する

    Args:
        city_name: 都市名
        character_type: "players" または "enemies"
        used_names: 既に使用された名前のセット（重複回避）

    Returns:
        選択された名前
    """
    if used_names is None:
        used_names = set()

    # 都市名に対応する名前リストを取得
    if (city_name in CITY_CHARACTER_NAMES
            and character_type in CITY_CHARACTER_NAMES[city_name]):
        available_names = CITY_CHARACTER_NAMES[city_name][character_type]
        # 未使用の名前から選択
        unused_names = [
            name for name in available_names if name not in used_names
        ]
        if unused_names:
            return random.choice(unused_names)
        else:
            # 全て使用済みの場合は番号付きで返す
            base_name = random.choice(available_names)
            counter = 2
            while f"{base_name}{counter}" in used_names:
                counter += 1
            return f"{base_name}{counter}"

    # フォールバック名
    fallback_names = {
        "players": ["Hero", "Warrior", "Knight", "Guardian"],
        "enemies": ["Foe", "Bandit", "Raider", "Villain"]
    }

    if character_type in fallback_names:
        available_names = fallback_names[character_type]
        unused_names = [
            name for name in available_names if name not in used_names
        ]
        if unused_names:
            return random.choice(unused_names)
        else:
            # フォールバック名も全て使用済みの場合
            base_name = random.choice(available_names)
            counter = 2
            while f"{base_name}{counter}" in used_names:
                counter += 1
            return f"{base_name}{counter}"

    return "Unknown"


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
        self.current_ai_enemy_index: Optional[int] = None

        # ゲーム状態ファイルのパス
        self.save_file_path = os.path.join("saves", "game_state.json")

        # savesフォルダが存在しない場合は作成
        os.makedirs(os.path.dirname(self.save_file_path), exist_ok=True)

    def initialize_default_state(self):
        """デフォルトのゲーム状態を初期化（中央座標系）"""
        # 座標変換器を使用
        coord_transformer = create_default_coordinate_transformer()

        # 都市を作成（中央座標系を使用）- 3つのみ
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
        }

        # 道路を作成（都市IDを使用）- 3都市の三角形構成
        self.roads = [
            Road(1, 2),  # Central - West
            Road(1, 3),  # Central - East
            Road(2, 3),  # West - East
        ]

        # プレイヤーを作成（Central と West に配置）
        used_names = set()

        central_player_name = get_character_name_for_city(
            "Central", "players", used_names
        )
        used_names.add(central_player_name)
        west_player_name = get_character_name_for_city(
            "West", "players", used_names
        )
        used_names.add(west_player_name)

        self.players = [
            # Central (0,0)
            Player(
                self.cities[1].x, self.cities[1].y, 1, name=central_player_name
            ),
            # West (-1,2)
            Player(
                self.cities[2].x, self.cities[2].y, 2,
                initiative=10, name=west_player_name
            ),
        ]

        # 敵を作成（East に1体配置）
        east_enemy_name = get_character_name_for_city(
            "East", "enemies", used_names
        )
        used_names.add(east_enemy_name)

        enemy1 = Enemy(
            self.cities[3].x, self.cities[3].y, 3,
            "aggressive", 1, name=east_enemy_name
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

            # 都市発見は別の状態で処理するためここでは実行しない

    def can_move_this_turn(self) -> bool:
        """このターンで移動可能かチェック"""
        if self.current_turn == "player":
            return not self.player_moved_this_turn
        else:
            return not self.enemy_moved_this_turn

    def should_discover_city(self) -> bool:
        """都市発見のタイミングかどうかをチェック"""
        return self.turn_counter % CITY_DISCOVERY_INTERVAL == 0

    def is_valid_city_placement_for_midpoint(
        self, new_city_x, new_city_y, city1_id, city2_id
    ):
        """中点配置用の都市配置有効性チェック（元の道路は除外）"""
        # 新しい都市から2つの既存都市への道路の座標
        city1 = self.cities[city1_id]
        city2 = self.cities[city2_id]

        new_road1_start = (new_city_x, new_city_y)
        new_road1_end = (city1.x, city1.y)
        new_road2_start = (new_city_x, new_city_y)
        new_road2_end = (city2.x, city2.y)

        # 既存の道路との交差をチェック（元の道路は除外）
        for road in self.roads:
            # 元の道路（city1_id - city2_id）は交差チェックから除外
            if (road.city1_id == city1_id and road.city2_id == city2_id) or (
                road.city1_id == city2_id and road.city2_id == city1_id
            ):
                continue

            road_city1 = self.cities[road.city1_id]
            road_city2 = self.cities[road.city2_id]
            existing_road_start = (road_city1.x, road_city1.y)
            existing_road_end = (road_city2.x, road_city2.y)

            # 新しい道路1が既存の道路と交差するかチェック
            if roads_intersect(
                new_road1_start, new_road1_end, existing_road_start, existing_road_end
            ):
                return False

            # 新しい道路2が既存の道路と交差するかチェック
            if roads_intersect(
                new_road2_start, new_road2_end, existing_road_start, existing_road_end
            ):
                return False

        # 新しい都市が既存の道路に近すぎないかチェック（元の道路は除外）
        min_distance_to_road = 20  # 最小距離（ピクセル）
        for road in self.roads:
            # 元の道路（city1_id - city2_id）は距離チェックから除外
            if (road.city1_id == city1_id and road.city2_id == city2_id) or (
                road.city1_id == city2_id and road.city2_id == city1_id
            ):
                continue

            road_city1 = self.cities[road.city1_id]
            road_city2 = self.cities[road.city2_id]
            existing_road_start = (road_city1.x, road_city1.y)
            existing_road_end = (road_city2.x, road_city2.y)

            # 新しい都市が既存の道路に近すぎる場合は無効
            if point_too_close_to_line(
                new_city_x,
                new_city_y,
                existing_road_start,
                existing_road_end,
                min_distance_to_road,
            ):
                return False

        # 新しい都市が既存の都市に近すぎないかチェック（接続先を除く）
        min_distance_to_city = 25  # 最小距離（ピクセル、少し短めに設定）
        for city in self.cities.values():
            if city.id not in [city1_id, city2_id]:  # 接続先の都市は除外
                distance_sq = (new_city_x - city.x) ** 2 + (new_city_y - city.y) ** 2
                if distance_sq < min_distance_to_city**2:
                    return False

        return True

    def plan_new_city(self):
        """新しい都市の配置を計画（GameStateは変更しない）"""
        if not self.roads:
            return None  # 既存道路がない場合は何もしない

        coord_transformer = create_default_coordinate_transformer()

        # 候補となる道路とその中点位置を生成
        candidate_positions = []

        for road in self.roads:
            city1 = self.cities[road.city1_id]
            city2 = self.cities[road.city2_id]

            # 2つの都市の中点を計算
            mid_x = (city1.x + city2.x) / 2
            mid_y = (city1.y + city2.y) / 2

            # 中点をタイル座標に変換
            mid_tile_x, mid_tile_y = coord_transformer.pixel_to_tile(mid_x, mid_y)

            # 中点付近の候補位置を生成（±1タイルの範囲）
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    candidate_tile_x = mid_tile_x + dx
                    candidate_tile_y = mid_tile_y + dy

                    # 既存都市の位置でないことを確認
                    occupied = False
                    for city in self.cities.values():
                        existing_tile_x, existing_tile_y = (
                            coord_transformer.pixel_to_tile(city.x, city.y)
                        )
                        if (
                            existing_tile_x == candidate_tile_x
                            and existing_tile_y == candidate_tile_y
                        ):
                            occupied = True
                            break

                    if not occupied:
                        # ピクセル座標に変換
                        candidate_x, candidate_y = coord_transformer.tile_to_pixel(
                            candidate_tile_x, candidate_tile_y
                        )

                        # 道路交差や距離チェックを実行
                        # 元の道路の両端都市とは接続しないので、一時的にダミーIDで検証
                        if self.is_valid_city_placement_for_midpoint(
                            candidate_x, candidate_y, road.city1_id, road.city2_id
                        ):
                            candidate_positions.append(
                                (
                                    candidate_tile_x,
                                    candidate_tile_y,
                                    candidate_x,
                                    candidate_y,
                                    road.city1_id,
                                    road.city2_id,
                                )
                            )

        if not candidate_positions:
            return None  # 候補位置がない場合は何もしない

        # ランダムに候補位置を選択
        chosen_tile_x, chosen_tile_y, chosen_x, chosen_y, city1_id, city2_id = (
            random.choice(candidate_positions)
        )

        # 新しい都市IDを生成
        new_city_id = max(self.cities.keys()) + 1

        # 都市名を生成
        city_names = [
            "Harbor",
            "Mountain",
            "Forest",
            "Desert",
            "Valley",
            "River",
            "Hill",
            "Lake",
            "Plains",
            "Canyon",
            "Bridge",
            "Crossing",
            "Junction",
            "Midway",
            "Gateway",
        ]
        used_names = {city.name for city in self.cities.values()}
        available_names = [name for name in city_names if name not in used_names]

        if available_names:
            new_city_name = random.choice(available_names)
        else:
            new_city_name = f"City{new_city_id}"

        # 新都市オブジェクトを作成（まだGameStateには追加しない）
        new_city = City(new_city_id, new_city_name, chosen_x, chosen_y)

        # 新都市に配置する敵キャラクターを生成（接続都市IDを渡す）
        new_enemy = self._create_enemy_for_new_city(
            chosen_x, chosen_y, new_city_id, [city1_id, city2_id]
        )

        # 発見計画の情報を返す
        return {
            "new_city": new_city,
            "connected_city_ids": [city1_id, city2_id],
            "connected_cities": [self.cities[city1_id], self.cities[city2_id]],
            "tile_position": (chosen_tile_x, chosen_tile_y),
            "new_enemy": new_enemy,
        }

    def apply_city_discovery(self, discovery_plan):
        """都市発見計画をGameStateに適用"""
        if not discovery_plan:
            return False

        new_city = discovery_plan["new_city"]
        city1_id, city2_id = discovery_plan["connected_city_ids"]
        new_enemy = discovery_plan["new_enemy"]
        chosen_tile_x, chosen_tile_y = discovery_plan["tile_position"]

        # 新都市をGameStateに追加
        self.cities[new_city.id] = new_city

        # 選択された2つの既存都市と新都市を道路で接続
        new_road1 = Road(city1_id, new_city.id)
        new_road2 = Road(city2_id, new_city.id)
        self.roads.append(new_road1)
        self.roads.append(new_road2)

        # 新都市に敵キャラクターを配置
        if new_enemy:
            self.enemies.append(new_enemy)
            print(f"New enemy ({new_enemy.ai_type}) spawned in {new_city.name}")

        print(
            f"New city discovered: {new_city.name} (ID: {new_city.id}) "
            f"at tile ({chosen_tile_x}, {chosen_tile_y})"
        )
        print(
            f"Connected to {self.cities[city1_id].name} (ID: {city1_id}) "
            f"and {self.cities[city2_id].name} (ID: {city2_id})"
        )

        # 自動セーブ
        self.auto_save()
        return True

    def discover_new_city(self):
        """新しい都市を発見して追加（後方互換性のため残存）"""
        # 計画を立てて即座に適用
        discovery_plan = self.plan_new_city()
        if discovery_plan:
            self.apply_city_discovery(discovery_plan)
        return discovery_plan

    def _create_enemy_for_new_city(
        self, x: float, y: float, city_id: int, connected_city_ids: List[int] = None
    ) -> Optional[Enemy]:
        """新都市用の敵キャラクターを生成"""
        if connected_city_ids is None:
            connected_city_ids = []

        # AIタイプをランダムに選択（バランスを考慮した重み付き）
        ai_types_with_weights = [
            ("random", 0.4),  # 40% - 最も一般的
            ("aggressive", 0.25),  # 25% - 積極的
            ("patrol", 0.20),  # 20% - パトロール
            ("defensive", 0.15),  # 15% - 防御的
        ]

        # 重み付きランダム選択
        weights = [weight for _, weight in ai_types_with_weights]
        ai_types = [ai_type for ai_type, _ in ai_types_with_weights]
        selected_ai_type = random.choices(ai_types, weights=weights)[0]

        # 敵のバリエーションのために異なる画像インデックスを使用
        # 既存の敵の数に基づいて画像を決定（1〜3段目をローテーション）
        image_index = (len(self.enemies) % 3) + 1  # 1, 2, 3をローテーション

        # 新都市の名前を取得
        new_city = self.get_city_by_id(city_id)
        city_name = new_city.name if new_city else "Unknown"

        # 既に使用されている名前を収集
        used_names = set()
        for enemy in self.enemies:
            used_names.add(enemy.name)
        for player in self.players:
            used_names.add(player.name)

        # 都市に基づいた敵の名前を選択
        enemy_name = get_character_name_for_city(
            city_name, "enemies", used_names
        )

        # 敵キャラクターを生成
        new_enemy = Enemy(
            x,
            y,
            current_city_id=city_id,
            ai_type=selected_ai_type,
            image_index=image_index,
            name=enemy_name,
        )

        # パトロールタイプの場合、近隣都市をパトロール経路に設定
        if selected_ai_type == "patrol" and connected_city_ids:
            # 新都市と接続都市を含むパトロール経路を設定
            new_enemy.patrol_city_ids = [city_id] + connected_city_ids[:2]  # 最大3都市
            new_enemy.patrol_index = 0

        return new_enemy

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
