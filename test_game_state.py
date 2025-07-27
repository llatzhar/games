import unittest
import os
import json
import tempfile
from game_state import GameState, City, Road, Player, Enemy

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
        expected = {
            'id': 1,
            'name': 'Tokyo',
            'x': 100.0,
            'y': 200.0,
            'size': 20
        }
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
        
        expected = {
            'city1_id': 1,
            'city2_id': 2
        }
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
    
    def test_player_serialization(self):
        """プレイヤーのシリアライゼーションテスト"""
        player = Player(50.0, 60.0, 1)
        data = player.to_dict()
        
        self.assertEqual(data['type'], 'player')
        self.assertEqual(data['x'], 50.0)
        self.assertEqual(data['y'], 60.0)
        self.assertEqual(data['current_city_id'], 1)
        
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
        self.assertEqual(enemy.image_index, 1)
        self.assertEqual(enemy.patrol_city_ids, [])
        self.assertEqual(enemy.patrol_index, 0)
        self.assertIsNone(enemy.last_player_position)
    
    def test_enemy_ai_types(self):
        """敵AIタイプのテスト"""
        ai_types = ["aggressive", "patrol", "defensive", "random"]
        for ai_type in ai_types:
            enemy = Enemy(0, 0, None, ai_type)
            self.assertEqual(enemy.ai_type, ai_type)
    
    def test_enemy_hover_info(self):
        """敵のホバー情報テスト"""
        enemy = Enemy(30.0, 40.0, 2, "aggressive", 1)
        info = enemy.get_hover_info()
        self.assertIn("Enemy (aggressive)", info)
        self.assertIn("Pursues players", info)
        
        # パトロールタイプの説明テスト
        patrol_enemy = Enemy(0, 0, None, "patrol")
        patrol_info = patrol_enemy.get_hover_info()
        self.assertIn("Patrols route", patrol_info)
    
    def test_enemy_serialization(self):
        """敵のシリアライゼーションテスト"""
        enemy = Enemy(30.0, 40.0, 2, "patrol", 2)
        enemy.patrol_city_ids = [1, 2, 3]
        enemy.patrol_index = 1
        
        data = enemy.to_dict()
        self.assertEqual(data['type'], 'enemy')
        self.assertEqual(data['ai_type'], 'patrol')
        self.assertEqual(data['patrol_city_ids'], [1, 2, 3])
        self.assertEqual(data['patrol_index'], 1)
        
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
        self.game_state.save_file_path = os.path.join(self.temp_dir, "test_game_state.json")
    
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
        
        # 都市数チェック
        self.assertEqual(len(self.game_state.cities), 6)
        
        # 道路数チェック
        self.assertEqual(len(self.game_state.roads), 9)
        
        # プレイヤー数チェック
        self.assertEqual(len(self.game_state.players), 2)
        
        # 敵数チェック
        self.assertEqual(len(self.game_state.enemies), 2)
        
        # 都市の存在確認
        city_names = [city.name for city in self.game_state.cities.values()]
        expected_cities = ["Kiyosu", "Nagoya", "Sakai", "Yamato", "Tutujigaoka", "Iwabuti"]
        for city_name in expected_cities:
            self.assertIn(city_name, city_names)
    
    def test_city_operations(self):
        """都市操作のテスト"""
        self.game_state.initialize_default_state()
        
        # IDで都市を取得
        city = self.game_state.get_city_by_id(1)
        self.assertIsNotNone(city)
        self.assertEqual(city.name, "Kiyosu")
        
        # 存在しない都市ID
        non_existent_city = self.game_state.get_city_by_id(999)
        self.assertIsNone(non_existent_city)
        
        # 都市表示名の取得
        display_name = self.game_state.get_city_display_name(1)
        self.assertEqual(display_name, "Kiyosu")
        
        # 存在しない都市の表示名
        non_existent_display_name = self.game_state.get_city_display_name(999)
        self.assertEqual(non_existent_display_name, "999")
    
    def test_road_connections(self):
        """道路接続のテスト"""
        self.game_state.initialize_default_state()
        
        # 接続されている都市のテスト
        self.assertTrue(self.game_state.are_cities_connected(1, 2))  # Kiyosu - Nagoya
        self.assertTrue(self.game_state.are_cities_connected(2, 1))  # 逆方向も確認
        
        # 接続されていない都市のテスト（直接は接続されていない）
        self.assertFalse(self.game_state.are_cities_connected(1, 6))  # Kiyosu - Iwabuti
        
        # 接続都市リストの取得
        connected_to_kiyosu = self.game_state.get_connected_city_ids(1)
        expected_connections = [2, 3, 4]  # Nagoya, Sakai, Yamato
        self.assertEqual(set(connected_to_kiyosu), set(expected_connections))
    
    def test_turn_switching(self):
        """ターン切り替えのテスト"""
        # 初期状態はプレイヤーターン
        self.assertEqual(self.game_state.current_turn, "player")
        self.assertEqual(self.game_state.turn_counter, 1)
        
        # プレイヤーターンから敵ターンへ
        self.game_state.switch_turn()
        self.assertEqual(self.game_state.current_turn, "enemy")
        self.assertEqual(self.game_state.turn_counter, 1)  # ターンカウンターは変わらない
        self.assertFalse(self.game_state.player_moved_this_turn)
        
        # 敵ターンからプレイヤーターンへ
        self.game_state.switch_turn()
        self.assertEqual(self.game_state.current_turn, "player")
        self.assertEqual(self.game_state.turn_counter, 2)  # ターンカウンターが増加
        self.assertFalse(self.game_state.enemy_moved_this_turn)
    
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
        self.assertEqual(battles[0]['city_id'], 1)
        self.assertEqual(len(battles[0]['players']), 1)
        self.assertEqual(len(battles[0]['enemies']), 1)
    
    def test_battle_execution(self):
        """戦闘実行のテスト"""
        self.game_state.initialize_default_state()
        
        # プレイヤーと敵を同じ都市に配置
        player = self.game_state.players[0]
        enemy = self.game_state.enemies[0]
        player.current_city_id = 1
        enemy.current_city_id = 1
        player.is_moving = False
        enemy.is_moving = False
        
        initial_player_life = player.life
        initial_enemy_life = enemy.life
        
        # 戦闘実行
        battle_result = self.game_state.execute_battle(1, [player], [enemy])
        
        # 戦闘後にライフが減少していることを確認
        self.assertLess(player.life, initial_player_life)
        self.assertLess(enemy.life, initial_enemy_life)
        
        # 戦闘ログが存在することを確認
        self.assertIsNotNone(battle_result)
        self.assertIn('log', battle_result)
        self.assertGreater(len(battle_result['log']), 0)
    
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

if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2)
