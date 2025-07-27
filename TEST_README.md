# ゲーム状態管理テストドキュメント

## 概要

このドキュメントでは、`game_state.py`モジュールの自動テストについて説明します。

## テストファイル構成

```
tests/
├── test_game_state.py      # メインテストファイル
├── run_tests.py           # カスタムテストランナー
├── test_config.py         # テスト設定
└── TEST_README.md         # このファイル
```

## テストの実行方法

### 1. 基本的な実行

```bash
# 全テストを実行
python -m unittest test_game_state.py

# 詳細出力で実行
python -m unittest test_game_state.py -v

# カスタムランナーで実行
python run_tests.py
```

### 2. 特定のテストクラスを実行

```bash
# Cityクラスのテストのみ
python run_tests.py TestCity

# GameStateクラスのテストのみ
python run_tests.py TestGameState
```

### 3. 特定のテストメソッドを実行

```bash
# 戦闘検出のテストのみ
python run_tests.py TestGameState.test_battle_detection

# 都市作成のテストのみ
python run_tests.py TestCity.test_city_creation
```

## テストカバレッジ

### テスト対象クラス

1. **City** - 都市クラス
   - 都市の作成
   - ホバー情報の取得
   - シリアライゼーション

2. **Road** - 道路クラス
   - 道路の作成
   - シリアライゼーション

3. **Player** - プレイヤークラス
   - プレイヤーの作成
   - ホバー情報の取得
   - シリアライゼーション

4. **Enemy** - 敵クラス
   - 敵の作成
   - AIタイプの設定
   - ホバー情報の取得
   - シリアライゼーション

5. **GameState** - ゲーム状態管理クラス
   - 初期化
   - デフォルト状態の作成
   - 都市操作
   - 道路接続
   - ターン切り替え
   - 移動フラグ管理
   - 戦闘検出と実行
   - キャラクター撃破処理
   - ファイル保存/読み込み
   - シリアライゼーション

### テストケース数

- **総テスト数**: 24個
- **Cityクラス**: 3個
- **Roadクラス**: 2個
- **Playerクラス**: 3個
- **Enemyクラス**: 4個
- **GameStateクラス**: 12個

## テスト項目詳細

### 1. 基本機能テスト

- オブジェクトの作成と初期化
- 属性値の正確性
- デフォルト値の確認

### 2. データ変換テスト

- 辞書への変換（`to_dict()`）
- 辞書からの復元（`from_dict()`）
- データの完全性確認

### 3. ゲームロジックテスト

- ターン切り替え
- 移動可能性判定
- 戦闘検出
- 戦闘実行
- キャラクター撃破

### 4. ファイルI/Oテスト

- JSONファイルへの保存
- JSONファイルからの読み込み
- 存在しないファイルの処理
- エラーハンドリング

### 5. データ整合性テスト

- 都市間の接続関係
- キャラクターの位置関係
- 戦闘時のキャラクター状態

## テスト環境

### 必要なモジュール

- `unittest` (Python標準ライブラリ)
- `tempfile` (Python標準ライブラリ)
- `json` (Python標準ライブラリ)
- `os` (Python標準ライブラリ)

### オプション

- `coverage` - コードカバレッジ測定用（別途インストール必要）

```bash
pip install coverage
python run_tests.py --coverage
```

## テストのベストプラクティス

### 1. テストの独立性

- 各テストは他のテストに依存しない
- `setUp()`と`tearDown()`でテスト環境を準備/クリーンアップ
- テンポラリファイルを使用してファイルシステムを汚染しない

### 2. 期待値の明確化

- 具体的な期待値を設定
- エラーケースも含めてテスト
- 境界値のテスト

### 3. テストデータの管理

- 予測可能なテストデータを使用
- ランダム要素は最小限に
- 実際のゲームデータに近い構造

## CI/CD統合

このテストスイートは継続的インテグレーション（CI）環境で実行できます：

```yaml
# .github/workflows/test.yml の例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Run tests
      run: |
        python -m unittest discover -s . -p "test_*.py" -v
```

## トラブルシューティング

### よくある問題

1. **ModuleNotFoundError**
   - `game_state.py`と同じディレクトリでテストを実行してください

2. **PermissionError (ファイルアクセス)**
   - テンポラリディレクトリの権限を確認してください
   - ウイルス対策ソフトウェアがファイルアクセスをブロックしていないか確認

3. **テストの実行時間が長い**
   - ファイルI/Oテストでテンポラリファイルが正しくクリーンアップされているか確認
   - 並列実行を検討（将来の拡張）

## 今後の拡張

1. **パフォーマンステスト**
   - 大量データでの動作確認
   - メモリ使用量の測定

2. **統合テスト**
   - 他のモジュールとの連携テスト
   - エンドツーエンドテスト

3. **プロパティベーステスト**
   - `hypothesis`ライブラリを使用した自動テストケース生成

4. **モックテスト**
   - 外部依存関係のモック化
   - より細かい単体テスト
