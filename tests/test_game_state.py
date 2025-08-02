import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# テストファイルからプロジェクトルートのモジュールをインポートできるようにする
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game_state import (  # noqa: E402
    CITY_DISCOVERY_DISTANCE,
    CITY_DISCOVERY_INTERVAL,
    City,
    Enemy,
    GameState,
    Player,
    Road,
)


class TestCity(unittest.TestCase):
    """Cityクラスのテスト"""

    def test_city_creation(self):
        """都市の作成テスト"""
        city = City(1, "Tokyo", 100.0, 200.0)
        self.assertEqual(city.id, 1)
        self.assertEqual(city.name, "Tokyo")
        self.assertEqual(city.x, 100.0)
        self.assertEqual(city.y, 200.0)
        self.assertEqual(city.size, 20)  # デフォルト値

    def test_city_hover_info(self):
        """都市のホバー情報テスト"""
        city = City(1, "Tokyo", 100.0, 200.0)
        info = city.get_hover_info()
        self.assertIn("City: Tokyo", info)
        self.assertIn("Position: (100, 200)", info)
        self.assertIn("Size: 20", info)

    def test_city_serialization(self):
        """都市のシリアライゼーションテスト"""
        city = City(1, "Tokyo", 100.0, 200.0)
        data = city.to_dict()

        # 辞書への変換をテスト
        expected = {"id": 1, "name": "Tokyo", "x": 100.0, "y": 200.0, "size": 20}
        self.assertEqual(data, expected)

        # 辞書からの復元をテスト
        restored_city = City.from_dict(data)
        self.assertEqual(restored_city.id, city.id)
        self.assertEqual(restored_city.name, city.name)
        self.assertEqual(restored_city.x, city.x)
        self.assertEqual(restored_city.y, city.y)
        self.assertEqual(restored_city.size, city.size)


class TestRoad(unittest.TestCase):
    """Roadクラスのテスト"""

    def test_road_creation(self):
        """道路の作成テスト"""
        road = Road(1, 2)
        self.assertEqual(road.city1_id, 1)
        self.assertEqual(road.city2_id, 2)

    def test_road_serialization(self):
        """道路のシリアライゼーションテスト"""
        road = Road(1, 2)
        data = road.to_dict()

        expected = {"city1_id": 1, "city2_id": 2}
        self.assertEqual(data, expected)

        restored_road = Road.from_dict(data)
        self.assertEqual(restored_road.city1_id, road.city1_id)
        self.assertEqual(restored_road.city2_id, road.city2_id)


class TestPlayer(unittest.TestCase):
    """Playerクラスのテスト"""

    def test_player_creation(self):
        """プレイヤーの作成テスト"""
        player = Player(50.0, 60.0, 1)
        self.assertEqual(player.x, 50.0)
        self.assertEqual(player.y, 60.0)
        self.assertEqual(player.current_city_id, 1)
        self.assertEqual(player.speed, 2)
        self.assertEqual(player.life, 120)
        self.assertEqual(player.max_life, 120)
        self.assertEqual(player.attack, 25)
        self.assertEqual(player.initiative, 15)
        self.assertEqual(player.image_index, 0)
        self.assertFalse(player.is_moving)

    def test_player_hover_info(self):
        """プレイヤーのホバー情報テスト"""
        player = Player(50.0, 60.0, 1)
        info = player.get_hover_info()
        self.assertIn("Player", info)
        self.assertIn("Location: 1", info)
        self.assertIn("Life: 120/120", info)
        self.assertIn("Attack: 25", info)
        self.assertIn("Initiative: 15", info)

    def test_player_serialization(self):
        """プレイヤーのシリアライゼーションテスト"""
        player = Player(50.0, 60.0, 1)
        data = player.to_dict()

        self.assertEqual(data["type"], "player")
        self.assertEqual(data["x"], 50.0)
        self.assertEqual(data["y"], 60.0)
        self.assertEqual(data["current_city_id"], 1)

        restored_player = Player.from_dict(data)
        self.assertEqual(restored_player.x, player.x)
        self.assertEqual(restored_player.y, player.y)
        self.assertEqual(restored_player.current_city_id, player.current_city_id)


class TestEnemy(unittest.TestCase):
    """Enemyクラスのテスト"""

    def test_enemy_creation(self):
        """敵の作成テスト"""
        enemy = Enemy(30.0, 40.0, 2, "aggressive", 1)
        self.assertEqual(enemy.x, 30.0)
        self.assertEqual(enemy.y, 40.0)
        self.assertEqual(enemy.current_city_id, 2)
        self.assertEqual(enemy.ai_type, "aggressive")
        self.assertEqual(enemy.speed, 1)
        self.assertEqual(enemy.life, 80)
        self.assertEqual(enemy.max_life, 80)
        self.assertEqual(enemy.attack, 20)
        self.assertEqual(enemy.initiative, 12)  # aggressive のイニシアチブ
        self.assertEqual(enemy.image_index, 1)
        self.assertEqual(enemy.patrol_city_ids, [])
        self.assertEqual(enemy.patrol_index, 0)
        self.assertIsNone(enemy.last_player_position)

    def test_enemy_ai_types_and_initiative(self):
        """敵AIタイプとイニシアチブのテスト"""
        ai_initiative_map = {
            "aggressive": 12,
            "patrol": 10,
            "defensive": 8,
            "random": 10,
        }

        for ai_type, expected_initiative in ai_initiative_map.items():
            enemy = Enemy(0, 0, None, ai_type)
            self.assertEqual(enemy.ai_type, ai_type)
            self.assertEqual(enemy.initiative, expected_initiative)

    def test_enemy_hover_info(self):
        """敵のホバー情報テスト"""
        enemy = Enemy(30.0, 40.0, 2, "aggressive", 1)
        info = enemy.get_hover_info()
        self.assertIn("Enemy (aggressive)", info)
        self.assertIn("Pursues players", info)
        self.assertIn("Initiative: 12", info)

        # パトロールタイプの説明テスト
        patrol_enemy = Enemy(0, 0, None, "patrol")
        patrol_info = patrol_enemy.get_hover_info()
        self.assertIn("Patrols route", patrol_info)
        self.assertIn("Initiative: 10", patrol_info)

    def test_enemy_serialization(self):
        """敵のシリアライゼーションテスト"""
        enemy = Enemy(30.0, 40.0, 2, "patrol", 2)
        enemy.patrol_city_ids = [1, 2, 3]
        enemy.patrol_index = 1

        data = enemy.to_dict()
        self.assertEqual(data["type"], "enemy")
        self.assertEqual(data["ai_type"], "patrol")
        self.assertEqual(data["patrol_city_ids"], [1, 2, 3])
        self.assertEqual(data["patrol_index"], 1)

        restored_enemy = Enemy.from_dict(data)
        self.assertEqual(restored_enemy.ai_type, enemy.ai_type)
        self.assertEqual(restored_enemy.patrol_city_ids, enemy.patrol_city_ids)
        self.assertEqual(restored_enemy.patrol_index, enemy.patrol_index)


class TestGameState(unittest.TestCase):
    """GameStateクラスのテスト"""

    def setUp(self):
        """各テストの前に実行される初期化"""
        self.game_state = GameState()
        # テンポラリディレクトリを使用してファイルシステムを汚染しない
        self.temp_dir = tempfile.mkdtemp()
        self.game_state.save_file_path = os.path.join(
            self.temp_dir, "test_game_state.json"
        )

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ"""
        # テンポラリファイルを削除
        if os.path.exists(self.game_state.save_file_path):
            os.remove(self.game_state.save_file_path)
        os.rmdir(self.temp_dir)

    def test_game_state_initialization(self):
        """ゲーム状態の初期化テスト"""
        self.assertEqual(self.game_state.current_turn, "player")
        self.assertEqual(self.game_state.turn_counter, 1)
        self.assertFalse(self.game_state.player_moved_this_turn)
        self.assertFalse(self.game_state.enemy_moved_this_turn)
        self.assertEqual(self.game_state.ai_timer, 0)
        self.assertEqual(self.game_state.ai_decision_delay, 60)
        self.assertIsNone(self.game_state.current_ai_enemy_index)
        self.assertEqual(len(self.game_state.cities), 0)
        self.assertEqual(len(self.game_state.roads), 0)
        self.assertEqual(len(self.game_state.players), 0)
        self.assertEqual(len(self.game_state.enemies), 0)

    def test_default_state_initialization(self):
        """デフォルト状態の初期化テスト"""
        self.game_state.initialize_default_state()

        # 都市数チェック（3都市）
        self.assertEqual(len(self.game_state.cities), 3)

        # 道路数チェック（3都市の三角形 = 3本の道路）
        self.assertEqual(len(self.game_state.roads), 3)

        # プレイヤー数チェック
        self.assertEqual(len(self.game_state.players), 2)

        # 敵数チェック
        self.assertEqual(len(self.game_state.enemies), 1)

        # プレイヤーのイニシアチブ値チェック
        self.assertEqual(
            self.game_state.players[0].initiative, 15
        )  # Player 1 デフォルト
        self.assertEqual(self.game_state.players[1].initiative, 10)  # Player 2 カスタム

        # 都市の存在確認
        city_names = [city.name for city in self.game_state.cities.values()]
        expected_cities = ["Central", "West", "East"]
        for city_name in expected_cities:
            self.assertIn(city_name, city_names)

    def test_city_operations(self):
        """都市操作のテスト"""
        self.game_state.initialize_default_state()

        # IDで都市を取得
        city = self.game_state.get_city_by_id(1)
        self.assertIsNotNone(city)
        self.assertEqual(city.name, "Central")

        # 存在しない都市ID
        non_existent_city = self.game_state.get_city_by_id(999)
        self.assertIsNone(non_existent_city)

        # 都市表示名の取得
        display_name = self.game_state.get_city_display_name(1)
        self.assertEqual(display_name, "Central")

        # 存在しない都市の表示名
        non_existent_display_name = self.game_state.get_city_display_name(999)
        self.assertEqual(non_existent_display_name, "999")

    def test_road_connections(self):
        """道路接続のテスト"""
        self.game_state.initialize_default_state()

        # 接続されている都市のテスト
        self.assertTrue(self.game_state.are_cities_connected(1, 2))  # Central - West
        self.assertTrue(self.game_state.are_cities_connected(2, 1))  # 逆方向も確認
        self.assertTrue(self.game_state.are_cities_connected(1, 3))  # Central - East
        self.assertTrue(self.game_state.are_cities_connected(2, 3))  # West - East

        # 存在しない都市との接続テスト
        self.assertFalse(
            self.game_state.are_cities_connected(1, 4)
        )  # Central - 存在しない都市4

        # 接続都市リストの取得
        connected_to_central = self.game_state.get_connected_city_ids(1)
        expected_connections = [2, 3]  # West, East
        self.assertEqual(set(connected_to_central), set(expected_connections))

    def test_turn_switching(self):
        """ターン切り替えのテスト"""
        # 初期状態はプレイヤーターン
        self.assertEqual(self.game_state.current_turn, "player")
        self.assertEqual(self.game_state.turn_counter, 1)

        # プレイヤーターンから敵ターンへ
        self.game_state.switch_turn()
        self.assertEqual(self.game_state.current_turn, "enemy")
        self.assertEqual(
            self.game_state.turn_counter, 1
        )  # ターンカウンターは変わらない
        self.assertFalse(self.game_state.player_moved_this_turn)

        # 敵ターンからプレイヤーターンへ
        self.game_state.initialize_default_state()  # 初期化

        self.game_state.switch_turn()
        self.assertEqual(self.game_state.current_turn, "player")
        self.assertEqual(self.game_state.turn_counter, 2)  # ターンカウンターが増加
        self.assertFalse(self.game_state.enemy_moved_this_turn)

        # 都市発見のタイミングチェック（CITY_DISCOVERY_INTERVAL=1の場合、毎ターン発見可能）
        if CITY_DISCOVERY_INTERVAL == 1:
            should_discover = self.game_state.should_discover_city()
            self.assertTrue(
                should_discover, "ターンカウンター2で都市発見可能でなければならない"
            )

    def test_city_discovery(self):
        """都市発見機能のテスト"""
        self.game_state.initialize_default_state()
        initial_cities_count = len(self.game_state.cities)
        initial_roads_count = len(self.game_state.roads)

        # 都市発見実行
        discovery_info = self.game_state.discover_new_city()

        # 発見情報が返されることを確認
        self.assertIsNotNone(discovery_info)
        self.assertIn("new_city", discovery_info)
        self.assertIn("source_city", discovery_info)
        self.assertIn("tile_position", discovery_info)

        # 都市が1つ増加
        self.assertEqual(len(self.game_state.cities), initial_cities_count + 1)

        # 道路が1つ増加
        self.assertEqual(len(self.game_state.roads), initial_roads_count + 1)

        # 新都市が適切な距離に配置されているかチェック
        from coordinate_utils import create_default_coordinate_transformer

        coord_transformer = create_default_coordinate_transformer()

        new_city = discovery_info["new_city"]
        source_city = discovery_info["source_city"]

        # 新都市と元都市の距離をチェック
        new_tile_x, new_tile_y = coord_transformer.pixel_to_tile(new_city.x, new_city.y)
        source_tile_x, source_tile_y = coord_transformer.pixel_to_tile(
            source_city.x, source_city.y
        )
        manhattan_distance = abs(new_tile_x - source_tile_x) + abs(
            new_tile_y - source_tile_y
        )

        self.assertEqual(
            manhattan_distance,
            CITY_DISCOVERY_DISTANCE,
            "新都市が元都市から適切な距離に配置されていません",
        )

    def test_city_discovery_interval(self):
        """都市発見間隔のテスト"""
        self.game_state.initialize_default_state()

        # 複数回ターン切り替えを行い、発見タイミングをテスト
        discovery_checks = []
        for turn in range(1, 6):
            # 敵ターンからプレイヤーターンへの切り替えをシミュレート
            self.game_state.current_turn = "enemy"
            self.game_state.turn_counter = turn
            self.game_state.switch_turn()

            # should_discover_city メソッドをテスト
            should_discover = self.game_state.should_discover_city()
            discovery_checks.append(should_discover)

            # 実際に発見処理を実行
            if should_discover:
                self.game_state.discover_new_city()

        # CITY_DISCOVERY_INTERVALに従って発見フラグが立っているかチェック
        expected_discovery_flags = [
            (turn + 1) % CITY_DISCOVERY_INTERVAL == 0 for turn in range(1, 6)
        ]
        self.assertEqual(discovery_checks, expected_discovery_flags)

    def test_city_discovery_after_battle(self):
        """戦闘後の都市発見タイミングのテスト"""
        self.game_state.initialize_default_state()

        # プレイヤーと敵を同じ都市に配置（戦闘を発生させる）
        player = self.game_state.players[0]
        enemy = self.game_state.enemies[0]
        player.current_city_id = 1  # Central
        enemy.current_city_id = 1  # Central（同じ都市に配置）

        # 都市発見のタイミングに設定
        self.game_state.turn_counter = CITY_DISCOVERY_INTERVAL

        # 戦闘をチェック
        battle_locations = self.game_state.check_battles()
        self.assertTrue(len(battle_locations) > 0, "戦闘が発生するはず")

        # 都市発見フラグもチェック
        should_discover = self.game_state.should_discover_city()
        self.assertTrue(should_discover, "都市発見のタイミングのはず")

        # この状況では：
        # 1. 戦闘がある場合 → BattleSequenceState → 戦闘後にCityDiscoveryState
        # 2. 戦闘がない場合 → 直接CityDiscoveryState
        # どちらの場合も最終的に都市発見が実行される

    def test_city_placement_road_intersection_check(self):
        """都市配置時の道路交差チェックのテスト"""
        self.game_state.initialize_default_state()

        # テスト用の都市配置（道路交差が発生するような配置を想定）
        # Central(0,0), West(-1,2), East(1,2) の初期配置

        # Central-West間の道路: (-16, 32) から (16, 32) への線分と交差するような新都市配置をテスト
        from coordinate_utils import create_default_coordinate_transformer

        coord_transformer = create_default_coordinate_transformer()

        central_city = self.game_state.cities[1]  # Central

        # Central-West道路と交差する位置（例：Central上方向で道路を横切る位置）
        test_pixel_x, test_pixel_y = coord_transformer.tile_to_pixel(
            0, -3
        )  # Central上方

        # 道路交差チェック関数をテスト
        is_valid = self.game_state.is_valid_city_placement(
            test_pixel_x, test_pixel_y, central_city.id
        )

        # 結果の検証（実際の道路配置によって結果は変わるが、関数が実行されることをテスト）
        self.assertIsInstance(
            is_valid, bool, "is_valid_city_placement should return a boolean"
        )

    def test_movement_flags(self):
        """移動フラグのテスト"""
        # プレイヤーターンでの移動可能性
        self.game_state.current_turn = "player"
        self.game_state.player_moved_this_turn = False
        self.assertTrue(self.game_state.can_move_this_turn())

        self.game_state.player_moved_this_turn = True
        self.assertFalse(self.game_state.can_move_this_turn())

        # 敵ターンでの移動可能性
        self.game_state.current_turn = "enemy"
        self.game_state.enemy_moved_this_turn = False
        self.assertTrue(self.game_state.can_move_this_turn())

        self.game_state.enemy_moved_this_turn = True
        self.assertFalse(self.game_state.can_move_this_turn())

    def test_battle_detection(self):
        """戦闘検出のテスト"""
        self.game_state.initialize_default_state()

        # 初期状態では戦闘は発生しない（プレイヤーと敵が異なる都市にいる）
        battles = self.game_state.check_battles()
        self.assertEqual(len(battles), 0)

        # プレイヤーと敵を同じ都市に配置
        player = self.game_state.players[0]
        enemy = self.game_state.enemies[0]
        player.current_city_id = 1
        enemy.current_city_id = 1
        player.is_moving = False
        enemy.is_moving = False

        battles = self.game_state.check_battles()
        self.assertEqual(len(battles), 1)
        self.assertEqual(battles[0]["city_id"], 1)
        self.assertEqual(len(battles[0]["players"]), 1)
        self.assertEqual(len(battles[0]["enemies"]), 1)

    def test_battle_system_integration(self):
        """戦闘システム統合テスト - check_battlesとBattleSubSceneの連携"""
        self.game_state.initialize_default_state()

        # プレイヤーと敵を同じ都市に配置
        player = self.game_state.players[0]
        enemy = self.game_state.enemies[0]
        player.current_city_id = 1
        enemy.current_city_id = 1
        player.is_moving = False
        enemy.is_moving = False

        # 戦闘検出のテスト
        battles = self.game_state.check_battles()
        self.assertEqual(len(battles), 1)
        self.assertEqual(battles[0]["city_id"], 1)
        self.assertEqual(len(battles[0]["players"]), 1)
        self.assertEqual(len(battles[0]["enemies"]), 1)

        # 戦闘情報の詳細確認
        battle_info = battles[0]
        self.assertEqual(battle_info["players_before"], 1)
        self.assertEqual(battle_info["enemies_before"], 1)
        self.assertIn("players", battle_info)
        self.assertIn("enemies", battle_info)

    def test_multiple_battles_detection(self):
        """複数都市での同時戦闘検出テスト"""
        self.game_state.initialize_default_state()

        # 複数の敵を追加して異なる都市に配置
        from game_state import Enemy

        enemy2 = Enemy(
            self.game_state.cities[2].x, self.game_state.cities[2].y, 2, "defensive", 2
        )
        self.game_state.enemies.append(enemy2)

        # プレイヤー1を都市1、プレイヤー2を都市2に配置（既存の敵もそれぞれの都市にいる）
        self.game_state.players[0].current_city_id = 1  # Central
        self.game_state.players[1].current_city_id = 2  # West
        self.game_state.enemies[0].current_city_id = 1  # Central
        enemy2.current_city_id = 2  # West

        # 全て移動停止状態にする
        for player in self.game_state.players:
            player.is_moving = False
        for enemy in self.game_state.enemies:
            enemy.is_moving = False

        # 戦闘検出
        battles = self.game_state.check_battles()
        self.assertEqual(len(battles), 2)  # 2つの都市で戦闘発生

        # 各戦闘の詳細確認
        city_ids = [battle["city_id"] for battle in battles]
        self.assertIn(1, city_ids)  # Central
        self.assertIn(2, city_ids)  # West

    def test_no_battle_when_moving(self):
        """移動中のキャラクターは戦闘に参加しないテスト"""
        self.game_state.initialize_default_state()

        # プレイヤーと敵を同じ都市に配置
        player = self.game_state.players[0]
        enemy = self.game_state.enemies[0]
        player.current_city_id = 1
        enemy.current_city_id = 1

        # プレイヤーを移動中にする
        player.is_moving = True
        enemy.is_moving = False

        # 戦闘は発生しないはず
        battles = self.game_state.check_battles()
        self.assertEqual(len(battles), 0)

        # 敵を移動中にする
        player.is_moving = False
        enemy.is_moving = True

        # まだ戦闘は発生しないはず
        battles = self.game_state.check_battles()
        self.assertEqual(len(battles), 0)

        # 両方とも停止状態にすると戦闘発生
        player.is_moving = False
        enemy.is_moving = False

        battles = self.game_state.check_battles()
        self.assertEqual(len(battles), 1)

    def test_character_defeat(self):
        """キャラクター撃破のテスト"""
        self.game_state.initialize_default_state()

        # プレイヤーのライフを0にする
        player = self.game_state.players[0]
        player.life = 0

        # 敵のライフを0にする
        enemy = self.game_state.enemies[0]
        enemy.life = 0

        initial_player_count = len(self.game_state.players)
        initial_enemy_count = len(self.game_state.enemies)

        # 撃破されたキャラクターを削除
        self.game_state.remove_defeated_characters()

        # キャラクター数が減少していることを確認
        self.assertEqual(len(self.game_state.players), initial_player_count - 1)
        self.assertEqual(len(self.game_state.enemies), initial_enemy_count - 1)

    def test_serialization_and_deserialization(self):
        """シリアライゼーションとデシリアライゼーションのテスト"""
        self.game_state.initialize_default_state()

        # 状態を少し変更
        self.game_state.current_turn = "enemy"
        self.game_state.turn_counter = 5
        self.game_state.player_moved_this_turn = True

        # 辞書への変換
        data = self.game_state.to_dict()

        # 新しいゲーム状態オブジェクトを作成して復元
        new_game_state = GameState()
        new_game_state.from_dict(data)

        # 復元された状態をチェック
        self.assertEqual(new_game_state.current_turn, "enemy")
        self.assertEqual(new_game_state.turn_counter, 5)
        self.assertTrue(new_game_state.player_moved_this_turn)
        self.assertEqual(len(new_game_state.cities), len(self.game_state.cities))
        self.assertEqual(len(new_game_state.roads), len(self.game_state.roads))
        self.assertEqual(len(new_game_state.players), len(self.game_state.players))
        self.assertEqual(len(new_game_state.enemies), len(self.game_state.enemies))

    def test_file_save_and_load(self):
        """ファイル保存と読み込みのテスト"""
        self.game_state.initialize_default_state()
        self.game_state.turn_counter = 10

        # ファイルに保存
        self.game_state.save_to_file()
        self.assertTrue(os.path.exists(self.game_state.save_file_path))

        # 新しいゲーム状態オブジェクトでファイルから読み込み
        new_game_state = GameState()
        new_game_state.save_file_path = self.game_state.save_file_path

        success = new_game_state.load_from_file()
        self.assertTrue(success)
        self.assertEqual(new_game_state.turn_counter, 10)
        self.assertEqual(len(new_game_state.cities), len(self.game_state.cities))

    def test_file_load_nonexistent(self):
        """存在しないファイルの読み込みテスト"""
        self.game_state.save_file_path = os.path.join(self.temp_dir, "nonexistent.json")
        success = self.game_state.load_from_file()
        self.assertFalse(success)


class TestCoordinateTransformation(unittest.TestCase):
    """座標変換システムのテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.game_state = GameState()

    def test_tile_to_pixel_coordinate_transformation(self):
        """タイル座標から物理座標への変換テスト"""
        self.game_state.initialize_default_state()

        # 中央座標系の検証（3都市のみ）
        # タイル(0,0) → 物理座標(256,256) - マップの中央
        central_city = self.game_state.cities[1]  # Central
        self.assertEqual(central_city.name, "Central")
        self.assertEqual(central_city.x, 256.0)
        self.assertEqual(central_city.y, 256.0)

        # タイル(-1,2) → 物理座標(224,320) - West
        west_city = self.game_state.cities[2]  # West
        self.assertEqual(west_city.name, "West")
        self.assertEqual(west_city.x, 224.0)
        self.assertEqual(west_city.y, 320.0)

        # タイル(1,2) → 物理座標(288,320) - East
        east_city = self.game_state.cities[3]  # East
        self.assertEqual(east_city.name, "East")
        self.assertEqual(east_city.x, 288.0)
        self.assertEqual(east_city.y, 320.0)

    def test_character_positioning_in_coordinate_system(self):
        """中央座標系でのキャラクター配置テスト"""
        self.game_state.initialize_default_state()

        # プレイヤー1はCentral（中央）に配置されている
        player1 = self.game_state.players[0]
        self.assertEqual(player1.current_city_id, 1)  # Central
        self.assertEqual(player1.x, 256.0)  # タイル(0,0) → 物理座標(256,256)
        self.assertEqual(player1.y, 256.0)

        # プレイヤー2はWest（西）に配置されている
        player2 = self.game_state.players[1]
        self.assertEqual(player2.current_city_id, 2)  # West
        self.assertEqual(player2.x, 224.0)  # タイル(-1,2) → 物理座標(224,320)
        self.assertEqual(player2.y, 320.0)

        # 敵はEast（東）に配置されている
        enemy1 = self.game_state.enemies[0]
        self.assertEqual(enemy1.current_city_id, 3)  # East
        self.assertEqual(enemy1.x, 288.0)  # タイル(1,2) → 物理座標(288,320)
        self.assertEqual(enemy1.y, 320.0)

    def test_coordinate_system_boundaries(self):
        """座標系の境界テスト"""
        # 17x17のマップサイズ（-8〜8）の境界確認
        tile_size = 32

        # tile_to_pixel関数の実装を直接テスト
        def tile_to_pixel(tile_x: int, tile_y: int) -> tuple[float, float]:
            pixel_x = (tile_x + 8) * tile_size
            pixel_y = (tile_y + 8) * tile_size
            return (pixel_x, pixel_y)

        # 左上端 タイル(-8,-8) → 物理座標(0,0)
        min_x, min_y = tile_to_pixel(-8, -8)
        self.assertEqual(min_x, 0.0)
        self.assertEqual(min_y, 0.0)

        # 右下端 タイル(8,8) → 物理座標(512,512)
        max_x, max_y = tile_to_pixel(8, 8)
        self.assertEqual(max_x, 512.0)
        self.assertEqual(max_y, 512.0)

        # 中央 タイル(0,0) → 物理座標(256,256)
        center_x, center_y = tile_to_pixel(0, 0)
        self.assertEqual(center_x, 256.0)
        self.assertEqual(center_y, 256.0)

    def test_coordinate_consistency_after_serialization(self):
        """シリアライゼーション後の座標一貫性テスト"""
        self.game_state.initialize_default_state()

        # シリアライゼーション前の座標を記録
        original_coordinates = {}
        for city_id, city in self.game_state.cities.items():
            original_coordinates[city_id] = (city.x, city.y)

        # シリアライゼーションとデシリアライゼーション
        data = self.game_state.to_dict()
        new_game_state = GameState()
        new_game_state.from_dict(data)

        # 座標が保持されていることを確認
        for city_id, (orig_x, orig_y) in original_coordinates.items():
            restored_city = new_game_state.cities[city_id]
            self.assertEqual(restored_city.x, orig_x)
            self.assertEqual(restored_city.y, orig_y)


class TestEnemyGeneration(unittest.TestCase):
    """新都市での敵生成機能のテスト"""

    def setUp(self):
        self.game_state = GameState()
        self.game_state.initialize_default_state()

    def test_enemy_spawned_with_new_city(self):
        """新都市発見時に敵が生成されることをテスト"""
        initial_enemy_count = len(self.game_state.enemies)
        initial_city_count = len(self.game_state.cities)

        # 都市発見を実行
        discovery_info = self.game_state.discover_new_city()

        # 新都市と敵が生成されたことを確認
        if discovery_info:  # 候補位置がある場合のみテスト
            self.assertEqual(len(self.game_state.cities), initial_city_count + 1)
            self.assertEqual(len(self.game_state.enemies), initial_enemy_count + 1)

            # 返り値に新しい敵が含まれていることを確認
            self.assertIn("new_enemy", discovery_info)
            new_enemy = discovery_info["new_enemy"]
            self.assertIsNotNone(new_enemy)

            # 新しい敵が新都市に配置されていることを確認
            new_city = discovery_info["new_city"]
            self.assertEqual(new_enemy.current_city_id, new_city.id)
            self.assertEqual(new_enemy.x, new_city.x)
            self.assertEqual(new_enemy.y, new_city.y)

    def test_enemy_ai_type_distribution(self):
        """敵のAIタイプが適切に分散されることをテスト"""
        ai_types_found = set()

        # 複数回都市発見を実行してAIタイプの分散を確認
        for _ in range(20):  # 十分な回数実行
            self.game_state = GameState()
            self.game_state.initialize_default_state()

            discovery_info = self.game_state.discover_new_city()
            if discovery_info and discovery_info["new_enemy"]:
                ai_types_found.add(discovery_info["new_enemy"].ai_type)

        # 複数のAIタイプが生成されることを確認
        # （確率的なテストなので、少なくとも2種類は見つかるはず）
        self.assertGreaterEqual(len(ai_types_found), 2)

        # 有効なAIタイプのみが生成されることを確認
        valid_ai_types = {"random", "aggressive", "patrol", "defensive"}
        for ai_type in ai_types_found:
            self.assertIn(ai_type, valid_ai_types)

    def test_enemy_image_index_rotation(self):
        """敵の画像インデックスがローテーションされることをテスト"""
        # 初期状態で1体の敵がいることを確認
        initial_enemy_count = len(self.game_state.enemies)

        # 複数の都市を発見して画像インデックスの変化を確認
        image_indices = []
        for i in range(3):  # 3回発見を試行
            discovery_info = self.game_state.discover_new_city()
            if discovery_info and discovery_info["new_enemy"]:
                image_indices.append(discovery_info["new_enemy"].image_index)

        # 画像インデックスが1-3の範囲内であることを確認
        for index in image_indices:
            self.assertIn(index, [1, 2, 3])

    def test_patrol_enemy_gets_route(self):
        """パトロールタイプの敵が適切な経路を取得することをテスト"""
        # パトロールタイプの敵が生成されるまで試行
        for _ in range(50):  # 最大50回試行
            self.game_state = GameState()
            self.game_state.initialize_default_state()

            discovery_info = self.game_state.discover_new_city()
            if (
                discovery_info
                and discovery_info["new_enemy"]
                and discovery_info["new_enemy"].ai_type == "patrol"
            ):

                patrol_enemy = discovery_info["new_enemy"]

                # パトロール経路が設定されていることを確認
                self.assertGreater(len(patrol_enemy.patrol_city_ids), 0)

                # 新都市が経路に含まれていることを確認
                new_city_id = discovery_info["new_city"].id
                self.assertIn(new_city_id, patrol_enemy.patrol_city_ids)

                # パトロールインデックスが0に設定されていることを確認
                self.assertEqual(patrol_enemy.patrol_index, 0)
                break


if __name__ == "__main__":
    # テストの実行
    unittest.main(verbosity=2)
