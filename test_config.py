# テスト設定ファイル
# このファイルはPythonの unittest ディスカバリーで使用されます

import unittest
import sys
import os

# テストディレクトリをPythonパスに追加
test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, test_dir)

# テストスイートの設定
class TestConfig:
    """テスト設定クラス"""
    
    # テストファイルのパターン
    TEST_PATTERN = 'test_*.py'
    
    # テストの開始ディレクトリ
    START_DIRECTORY = '.'
    
    # テストの詳細レベル
    VERBOSITY = 2
    
    # テストの並列実行（将来の拡張用）
    PARALLEL = False
    
    # テストデータディレクトリ
    TEST_DATA_DIR = os.path.join(test_dir, 'test_data')
    
    # 一時ファイルのクリーンアップ
    CLEANUP_TEMP_FILES = True

def load_tests(loader, tests, pattern):
    """unittest discover用のload_tests関数"""
    suite = unittest.TestSuite()
    
    # game_stateモジュールのテストを追加
    from test_game_state import (
        TestCity, TestRoad, TestPlayer, TestEnemy, TestGameState
    )
    
    # 各テストクラスを追加
    suite.addTests(loader.loadTestsFromTestCase(TestCity))
    suite.addTests(loader.loadTestsFromTestCase(TestRoad))
    suite.addTests(loader.loadTestsFromTestCase(TestPlayer))
    suite.addTests(loader.loadTestsFromTestCase(TestEnemy))
    suite.addTests(loader.loadTestsFromTestCase(TestGameState))
    
    return suite

if __name__ == '__main__':
    # このファイルが直接実行された場合はテストを実行
    unittest.main()
