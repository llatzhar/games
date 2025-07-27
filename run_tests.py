#!/usr/bin/env python3
"""
ゲーム状態管理のテストランナー

使用方法:
    python run_tests.py              # 全テストを実行
    python run_tests.py -v           # 詳細出力で実行
    python run_tests.py TestCity     # 特定のテストクラスのみ実行
    python run_tests.py TestGameState.test_battle_detection  # 特定のテストメソッドのみ実行
"""

import unittest
import sys
import os

def run_tests():
    """テストを実行する"""
    
    # テストディスカバリー
    loader = unittest.TestLoader()
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        # 特定のテストクラスまたはメソッドが指定された場合
        test_name = sys.argv[1]
        if test_name == '-v':
            # 詳細出力フラグ
            verbosity = 2
            suite = loader.discover('.', pattern='test_*.py')
        else:
            # 特定のテストを実行
            verbosity = 2
            try:
                # test_game_state.TestClassまたはtest_game_state.TestClass.test_methodの形式
                if '.' in test_name and not test_name.startswith('test_'):
                    test_name = f'test_game_state.{test_name}'
                elif not test_name.startswith('test_') and not '.' in test_name:
                    test_name = f'test_game_state.{test_name}'
                
                suite = loader.loadTestsFromName(test_name)
            except Exception as e:
                print(f"エラー: テスト '{test_name}' が見つかりません: {e}")
                return False
    else:
        # 全テストを実行
        verbosity = 1
        suite = loader.discover('.', pattern='test_*.py')
    
    # テストランナーの作成と実行
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # 結果のサマリー表示
    print("\n" + "="*60)
    print("テスト結果サマリー:")
    print(f"実行されたテスト数: {result.testsRun}")
    print(f"失敗したテスト数: {len(result.failures)}")
    print(f"エラーが発生したテスト数: {len(result.errors)}")
    
    if result.failures:
        print("\n失敗したテスト:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"  - {test}: {error_msg}")
    
    if result.errors:
        print("\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"  - {test}: {error_msg}")
    
    if result.wasSuccessful():
        print("\n🎉 全てのテストが成功しました！")
        return True
    else:
        print("\n❌ 一部のテストが失敗しました。")
        return False

def run_coverage():
    """カバレッジ付きでテストを実行（coverageパッケージが必要）"""
    try:
        import coverage
        
        # カバレッジの設定
        cov = coverage.Coverage(source=['game_state'])
        cov.start()
        
        # テスト実行
        success = run_tests()
        
        # カバレッジ停止と報告
        cov.stop()
        cov.save()
        
        print("\n" + "="*60)
        print("コードカバレッジレポート:")
        cov.report(show_missing=True)
        
        # HTMLレポート生成
        cov.html_report(directory='coverage_html')
        print("\nHTMLレポートが 'coverage_html' ディレクトリに生成されました。")
        
        return success
        
    except ImportError:
        print("注意: coverageパッケージがインストールされていません。")
        print("カバレッジレポートを生成するには 'pip install coverage' を実行してください。")
        return run_tests()

if __name__ == '__main__':
    # カバレッジオプションの確認
    if '--coverage' in sys.argv:
        sys.argv.remove('--coverage')
        success = run_coverage()
    else:
        success = run_tests()
    
    # 終了コード
    sys.exit(0 if success else 1)
