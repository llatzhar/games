# Pyxel ターンベースストラテジーゲーム

## 概要
Pyxelライブラリを使用したターンベース戦略ゲームです。プレイヤーと敵AIが交互に行動し、都市間を移動して戦略的な位置取りを行います。

[![Tests](https://github.com/llatzhar/games/actions/workflows/test.yml/badge.svg)](https://github.com/llatzhar/games/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/llatzhar/games/branch/main/graph/badge.svg)](https://codecov.io/gh/llatzhar/games)

## 機能

### 基本システム
- **ターンベースゲームプレイ**: プレイヤーターンと敵ターンが交互に切り替わる
- **都市ベースマップ**: 6つの都市（Town A～F）が道路で接続された2x3グリッド
- **キャラクター移動**: 接続された都市間のみ移動可能
- **重複防止システム**: 同じ都市に複数キャラクターがいる場合の自動配置調整
- **カメラシステム**: WASDキーでマップを自由に移動

### 敵AIシステム

#### AI行動タイプ
1. **Aggressive AI（アグレッシブ）**
   - **色**: 赤色インジケーター
   - **行動**: 最も近いプレイヤーを積極的に追跡
   - **特徴**: BFSアルゴリズムを使用した最短経路探索
   - **戦略**: プレイヤーに圧力をかけ続ける攻撃的な行動

2. **Patrol AI（パトロール）**
   - **色**: ライトブルーインジケーター
   - **行動**: 事前定義されたルートを循環移動
   - **ルート**: Town F → Town D → Town B → Town E → 繰り返し
   - **特徴**: 予測可能だが一定の脅威を維持

3. **Defensive AI（ディフェンシブ）**
   - **色**: 緑色インジケーター
   - **行動**: プレイヤーから最も遠い場所へ移動
   - **特徴**: 接続された都市の中で最適な逃走先を選択
   - **戦略**: 直接対決を避ける回避行動

4. **Random AI（ランダム）**
   - **色**: ピンクインジケーター
   - **行動**: 接続された都市からランダムに選択
   - **特徴**: 予測不可能な動きで戦略に変化を与える

#### AI視覚システム
- **AIタイプインジケーター**: 各敵の上に小さな色付きの円で行動タイプを表示
- **思考インジケーター**: 敵の決定時間中に点滅する白い円を表示
- **AI凡例**: デバッグ情報内に色と行動タイプの対応表を表示
- **AIタイマー**: 敵ターン中の思考時間をリアルタイム表示

### カメラ追従システム
- **敵ターン中の自動追従**: 敵が選択・移動される際にカメラが自動的に追従
- **スムーズな移動**: カメラは対象キャラクターを中央に捉えながらスムーズに移動
- **手動操作制限**: 敵ターン中の追従時は手動カメラ操作が無効化
- **ターン切り替え時のリセット**: ターンが切り替わる際に追従状態がクリア
- **視覚的フィードバック**: デバッグ情報で追従状態がリアルタイム表示

#### AI技術仕様
- **パスファインディング**: BFS（幅優先探索）アルゴリズムによる最短経路計算
- **決定遅延**: 2秒間（60フレーム）の思考時間でリアルな意思決定を演出
- **ランダム選択**: 複数の敵から公平にランダム選択してターン実行
- **状態管理**: 各AIの内部状態（パトロールインデックス等）を適切に管理

## 操作方法

### 基本操作
- **マウスクリック**: キャラクター選択・移動先指定
- **WASD**: カメラ移動（敵ターン中の追従時は無効）
- **ESC**: 選択解除
- **Space**: ターンスキップ
- **V**: デバッグ情報表示切り替え
- **Q**: タイトル画面に戻る

### カメラ操作
- **プレイヤーターン**: WASDキーで自由にカメラを操作可能
- **敵ターン**: 敵キャラクターに自動的にカメラが追従（手動操作無効）
- **追従解除**: ターン切り替え時に自動的に追従状態がリセット

### ゲームプレイ
1. **プレイヤーターン**: 
   - キャラクターをクリックして選択
   - 接続された都市をクリックして移動
   - 移動完了で自動的に敵ターンに切り替わり

2. **敵ターン**: 
   - AI自動実行（2秒の思考時間後）
   - 敵の行動タイプに応じた戦略的移動
   - 移動完了で自動的にプレイヤーターンに切り替わり

## 技術仕様

### 開発環境
- **言語**: Python 3.x
- **ライブラリ**: Pyxel
- **アーキテクチャ**: オブジェクト指向設計（Sceneパターン）

### ファイル構成
- `game.py`: メインゲームエンジンとシーン管理
- `map.py`: マップシーン、キャラクタークラス、AI実装
- `resources.pyxres`: スプライトリソース
- `README.md`: プロジェクトドキュメント

### クラス設計
- `Character`: キャラクターの基底クラス
- `Player`: プレイヤーキャラクター（速度: 2）
- `Enemy`: 敵キャラクター（速度: 1、AI搭載）
- `City`: 都市オブジェクト
- `Road`: 都市間接続
- `MapScene`: メインゲームシーン

## map.py モジュール仕様

### 概要
`map.py`はゲームのメインシーンを管理するモジュールで、`MapScene`クラスによってゲームプレイの中核機能を提供します。

### 主要クラス: MapScene

#### 基本機能と責任
1. **ゲーム状態管理**
   - `GameState`オブジェクトの初期化と管理
   - セーブ/ロード機能の呼び出し
   - ターン管理（プレイヤー/敵ターン切り替え）
   - 移動可能状態の判定

2. **マップ表示システム**
   - 30x30グリッドのマップ生成と描画
   - タイルベース表示（16x16ピクセル）
   - カメラシステム（視点移動と追従）
   - 画面カリング（表示範囲最適化）

3. **キャラクター管理**
   - プレイヤー・敵キャラクターの描画と位置管理
   - 移動アニメーション処理
   - 重複防止システム（同一都市内での配置調整）
   - キャラクター選択とUI表示

#### カメラシステム
- **手動操作**: WASDキーによる自由視点移動
- **自動追従**: 敵ターン時のキャラクター追従
- **スムーズ移動**: 目標位置への滑らかな移動
- **範囲制限**: マップ境界内でのカメラ位置制限
- **状態管理**: 追従対象の設定・解除

#### AI実行エンジン
1. **AI決定システム**
   - 各AIタイプ（aggressive, patrol, defensive, random）の行動決定
   - パスファインディング（BFS）の実行
   - 移動可能性チェック（都市間接続確認）
   - AI思考遅延の演出

2. **AIタイプ別実装**
   - **Aggressive**: プレイヤーへの最短経路探索
   - **Patrol**: 固定ルート循環移動
   - **Defensive**: プレイヤーから最遠地点選択
   - **Random**: 接続都市からランダム選択

#### 戦闘システム統合
- **戦闘検出**: ターン終了時の同一都市チェック
- **戦闘シーケンス**: `BattleSubScene`との連携
- **結果処理**: 戦闘後のキャラクター状態更新
- **カメラ制御**: 戦闘時の視点移動

#### 入力処理システム
1. **マウス操作**
   - キャラクター選択（クリック判定）
   - 移動先指定（都市クリック）
   - 画面座標→ワールド座標変換

2. **キーボード操作**
   - カメラ移動（WASD）
   - ターンスキップ（Space）
   - 選択解除（ESC）
   - デバッグ表示（V）
   - タイトル復帰（Q）

#### 状態遷移フロー
```
ゲーム開始 → MapScene初期化
    ↓
セーブデータ確認 → ロード/新規作成
    ↓
プレイヤーターン開始
    ↓
入力受付 → キャラクター選択 → 移動実行
    ↓
ターン切り替え → 戦闘チェック
    ↓
戦闘あり: BattleSubScene → 戦闘なし: 敵ターン
    ↓
敵AI実行 → 移動実行
    ↓
ターン切り替え → 戦闘チェック
    ↓
（ループ）
```

#### 他モジュールとの依存関係

##### 依存するモジュール
- **game_state.py**: ゲーム状態管理、セーブ/ロード、戦闘計算
- **battle.py**: 戦闘シーン表示（`BattleSubScene`）
- **cutin.py**: ターン切り替え演出（`CutinSubScene`）
- **hover_info.py**: ホバー情報表示（`HoverInfo`）
- **game.py**: シーン基底クラス、画面定数

##### 提供する機能
- **メインゲームループ**: ターンベースゲームプレイ
- **ユーザインターフェース**: 操作可能なゲーム画面
- **AI実行環境**: 敵キャラクターの自動行動

#### データ管理
1. **座標系**
   - ワールド座標: マップ上の絶対位置
   - スクリーン座標: 表示画面上の相対位置
   - カメラオフセット: 座標変換計算

2. **状態フラグ**
   - `current_turn`: 現在のターン（"player"/"enemy"）
   - `player_moved_this_turn`/`enemy_moved_this_turn`: ターン内移動完了フラグ
   - `is_processing_battles`: 戦闘処理中フラグ
   - `selected_player`/`selected_enemy`: 選択中キャラクター

3. **タイマー管理**
   - `ai_timer`: AI思考時間計測
   - `click_timer`: クリック座標表示時間
   - `battle_camera_timer`: 戦闘時カメラ移動待機

#### 描画システム
1. **レイヤー構成**
   - 背景: マップタイル（壁・床）
   - 道路: 都市間接続線
   - 都市: 青色円とラベル
   - キャラクター: プレイヤー・敵（スプライト）
   - UI: ライフバー、選択枠、ホバー情報

2. **視覚効果**
   - アニメーション: キャラクタースプライト（2フレーム）
   - 点滅効果: 選択キャラクターの枠線
   - 色分け表示: AIタイプインジケーター
   - 思考演出: AI決定時の点滅円

#### デバッグ機能
- **3ページ構成**: 基本情報/カメラ・マップ/キャラクター・AI
- **リアルタイム表示**: 座標、状態、ターン情報
- **AI状態可視化**: 思考状態、行動タイプ、決定過程
- **パフォーマンス監視**: フレームレート、処理負荷

### 設計思想
- **責任分離**: 描画・ロジック・状態管理の明確な分離
- **拡張性**: 新AIタイプやマップサイズへの対応
- **ユーザビリティ**: 直感的な操作と視覚フィードバック
- **保守性**: モジュール間の疎結合と明確なインターフェース

## StateMachineパターン適用設計

### 概要
現在のmap.pyの複雑な状態管理を、StateMachineパターンで整理することで、より保守性の高い設計に改善できます。

### 主要状態（State）の定義

#### 1. PlayerTurnState（プレイヤーターン状態）
```python
class PlayerTurnState(GameState):
    """プレイヤーが操作可能な状態"""
    
    # 責任範囲
    - プレイヤーキャラクターの選択処理
    - 移動先都市の選択処理
    - 移動可能性の検証
    - キャラクター移動アニメーション管理
    
    # 状態遷移条件
    - プレイヤー移動完了 → TransitionState
    - ターンスキップ（Space） → TransitionState
    - ゲーム終了（Q） → ExitState
    
    # 入力処理
    - マウスクリック: キャラクター/都市選択
    - ESC: 選択解除
    - カメラ操作: 全方向有効
```

#### 2. EnemyTurnState（敵ターン状態）
```python
class EnemyTurnState(GameState):
    """AIが自動実行される状態"""
    
    # 責任範囲
    - AI思考時間管理（2秒以内に意思決定）
    - 敵キャラクター選択（ランダム）
    - AI行動決定（4タイプの実装）
    - 敵移動アニメーション管理
    - カメラ自動追従制御
    
    # 状態遷移条件
    - 敵移動完了 → TransitionState
    - ターンスキップ（Space） → TransitionState
    - ゲーム終了（Q） → ExitState
    
    # 入力処理
    - カメラ操作: 追従中は無効、手動選択時のみ有効
    - 敵選択: クリックによる手動選択（デバッグ用）
```

#### 3. TransitionState（ターン切り替え状態）
```python
class TransitionState(GameState):
    """ターン間の遷移処理状態"""
    
    # 責任範囲
    - 戦闘発生チェック
    - 次ターンの決定
    - ゲーム終了条件判定
    - 自動セーブ実行
    
    # 状態遷移条件
    - 戦闘発生 → BattleSequenceState
    - 戦闘なし + プレイヤーターン → CutinState(PLAYER_TURN)
    - 戦闘なし + 敵ターン → CutinState(ENEMY_TURN)
    - 全プレイヤー死亡 → GameOverState
    - 全敵死亡 → VictoryState
    
    # 特徴
    - 一瞬で完了する処理状態
    - ユーザー入力は受け付けない
```

#### 4. BattleSequenceState（戦闘シーケンス状態）
```python
class BattleSequenceState(GameState):
    """複数戦闘の連続処理状態"""
    
    # 責任範囲
    - 戦闘場所リストの管理
    - 戦闘間のカメラ移動
    - BattleSubSceneの起動・管理
    - 戦闘結果の統合処理
    
    # 状態遷移条件
    - 全戦闘完了 → CutinState(次ターン)
    - 戦闘中断（Q） → ExitState
    
    # サブ状態
    - CameraMovingSubState: 戦闘地点への移動
    - BattleSubState: 個別戦闘実行
    - ResultProcessingSubState: 戦闘結果処理
```

#### 5. CutinState（カットイン演出状態）
```python
class CutinState(GameState):
    """ターン切り替え演出状態"""
    
    # 責任範囲
    - CutinSubSceneの管理
    - 演出完了の監視
    - 次状態への遷移制御
    
    # 状態遷移条件
    - 演出完了 → PlayerTurnState/EnemyTurnState
    - 演出中断（Q） → ExitState
    
    # パラメータ
    - next_turn: "player" | "enemy"
    - cutin_text: 表示テキスト
```

#### 6. GameOverState（ゲーム終了状態）
```python
class GameOverState(GameState):
    """ゲーム終了表示状態"""
    
    # 責任範囲
    - 勝敗結果の表示
    - 終了メッセージ表示
    - タイトル復帰待機
    
    # 状態遷移条件
    - Q押下 → ExitState
    
    # 種類
    - VictoryState: 勝利時
    - DefeatState: 敗北時
```

#### 7. PausedState（一時停止状態）
```python
class PausedState(GameState):
    """ゲーム一時停止状態"""
    
    # 責任範囲
    - ポーズメニュー表示
    - 設定変更処理
    - セーブ/ロード処理
    
    # 状態遷移条件
    - 再開 → 前の状態に復帰
    - タイトル → ExitState
```

### 状態遷移図
```
                   ゲーム開始
                      ↓
                 PlayerTurnState ←─────┐
                      ↓               │
                 TransitionState      │
                   ↓        ↓         │
            CutinState  BattleSequenceState
                   ↓        ↓         │
              EnemyTurnState ←────────┘
                      ↓
                 TransitionState
                      ↓
               GameOverState/VictoryState
                      ↓
                   ExitState
```

### 各状態の詳細実装方針

#### 状態基底クラス
```python
class MapGameState(ABC):
    def __init__(self, context):
        self.context = context  # MapSceneへの参照
    
    @abstractmethod
    def enter(self):
        """状態開始時の処理"""
        pass
    
    @abstractmethod
    def update(self):
        """毎フレーム更新処理"""
        pass
    
    @abstractmethod
    def handle_input(self, input_event):
        """入力処理"""
        pass
    
    @abstractmethod
    def exit(self):
        """状態終了時の処理"""
        pass
    
    def transition_to(self, new_state):
        """状態遷移実行"""
        self.context.change_state(new_state)
```

#### 状態管理コンテキスト
```python
class MapScene(Scene):
    def __init__(self):
        super().__init__()
        self.current_state = None
        self.game_state = GameState()
        # ... その他の初期化
        
        # 初期状態設定
        self.change_state(PlayerTurnState(self))
    
    def change_state(self, new_state):
        if self.current_state:
            self.current_state.exit()
        self.current_state = new_state
        new_state.enter()
    
    def update(self):
        if self.current_state:
            return self.current_state.update()
        return self
```

### StateMachine適用のメリット

#### 1. 責任の明確化
- 各状態が特定の局面のみを担当
- 状態間の依存関係が明確
- テストが容易になる

#### 2. 拡張性の向上
- 新しい状態の追加が容易
- 既存状態への影響を最小化
- 状態遷移ロジックの変更が局所化

#### 3. バグの削減
- 不正な状態遷移の防止
- 各状態での処理が明確
- デバッグ時の状態追跡が容易

#### 4. 保守性の向上
- コードの可読性向上
- 機能追加時の影響範囲特定
- リファクタリングの安全性

### 実装時の注意点

#### 1. 状態間のデータ共有
- GameStateオブジェクトで共有データを管理
- 状態固有データは各状態内で管理
- 状態遷移時のデータ受け渡し方法の設計

#### 2. パフォーマンス考慮
- 状態遷移のオーバーヘッド最小化
- 頻繁な状態変更の回避
- メモリ使用量の最適化

#### 3. デバッグ支援
- 状態履歴の記録
- 状態遷移ログの出力
- 現在状態の可視化

## 今後の拡張可能性
- 新しいAI行動タイプの追加
- より複雑なマップレイアウト
- 戦闘システムの実装
- マルチプレイヤー対応

## 開発・テスト

### テストの実行

#### 基本的なテスト実行
```bash
# 全テストを実行
python -m unittest discover -s . -p "test_*.py"

# 詳細出力で実行
python -m unittest discover -s . -p "test_*.py" -v

# 特定のテストクラスのみ実行
python -m unittest test_game_state.TestCity

# 特定のテストメソッドのみ実行
python -m unittest test_game_state.TestCity.test_city_creation
```

#### カバレッジ付きテスト実行
```bash
# カバレッジ付きでテストを実行
coverage run -m unittest discover -s . -p "test_*.py"

# カバレッジレポートを表示
coverage report -m

# HTMLレポートを生成
coverage html
```

#### 便利なスクリプト

**Windows (PowerShell):**
```powershell
# 依存関係のインストール
.\test.ps1 install

# テスト実行
.\test.ps1 test

# カバレッジ付きテスト
.\test.ps1 test-coverage

# コードフォーマット
.\test.ps1 format

# リンティング(pip install flake8)
.\test.ps1 lint
```

**Linux/macOS (Make):**
```bash
# 依存関係のインストール
make install

# テスト実行
make test

# カバレッジ付きテスト
make test-coverage

# コードフォーマット
make format

# リンティング
make lint
```

### CI/CDパイプライン

このプロジェクトはGitHub Actionsを使用して自動テストとコード品質チェックを実行します：

#### 自動実行されるチェック
- **テスト実行**: Python 3.8, 3.9, 3.10, 3.11での単体テスト
- **コードカバレッジ**: カバレッジレポートの生成とCodecovへのアップロード
- **コード品質**:
  - `flake8`によるリンティング
  - `black`によるコードフォーマットチェック
  - `isort`によるインポート順序チェック

#### トリガー条件
- `main`、`develop`ブランチへのプッシュ
- `main`ブランチに対するプルリクエスト

#### 設定ファイル
- `.github/workflows/test.yml`: GitHub Actionsワークフロー設定
- `pyproject.toml`: コード品質ツールの設定
- `requirements.txt`: 開発依存関係

### コード品質

#### フォーマッティング
- **Black**: コードフォーマッター（行長88文字）
- **isort**: インポート文の並び替え

#### リンティング
- **flake8**: PEP8準拠チェックとコード品質検査

#### 推奨する開発フロー
1. コードを書く
2. フォーマットを適用: `.\test.ps1 format` または `make format`
3. リンティングチェック: `.\test.ps1 lint` または `make lint`
4. テスト実行: `.\test.ps1 test` または `make test`
5. カバレッジ確認: `.\test.ps1 test-coverage` または `make test-coverage`
6. コミット・プッシュ

### テスト構成

#### テストファイル
- `test_game_state.py`: ゲーム状態管理のテスト
- `run_tests.py`: テストランナー（詳細出力、特定テスト実行対応）

#### テスト対象
- **City**: 都市オブジェクトの作成、シリアライゼーション、ホバー情報
- **Road**: 道路オブジェクトの作成、シリアライゼーション
- **Player**: プレイヤーオブジェクトの作成、ステータス、移動
- **Enemy**: 敵オブジェクトの作成、AIタイプ、行動パターン
- **GameState**: ゲーム全体の状態管理、ファイル保存/読み込み、戦闘システム

#### カバレッジ目標
- 全体カバレッジ: 90%以上
- 重要なクラス（GameState, Player, Enemy）: 95%以上
- AI学習機能の追加

