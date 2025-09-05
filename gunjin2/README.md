# 軍人将棋 (Gunjin Shogi) - LAN対戦版

## 概要
LAN内で通信対戦ができる軍人将棋ゲームです。Pygameを使用してグラフィカルなインターフェースを提供し、内蔵サーバー機能により簡単に対戦できます。

## 特徴
- **LAN内での2人対戦**: ホスト/クライアント方式で簡単接続
- **内蔵サーバー機能**: 別途サーバーソフト不要
- **本格的な軍人将棋**: 16種類23個の駒による戦略ゲーム
- **デジタル版独自の表示方式**: 自分の駒は表向き（種類が見える）、相手の駒は伏せて表示
- **完全隠蔽情報**: 相手の駒の種類は戦闘後も不明
- **リアルタイム同期**: 駒移動とゲーム状態を即座に同期
- **日本語UI**: 完全日本語対応インターフェース

## システム要件
- Python 3.8以上
- pygame 2.0以上
- LAN接続環境
- 日本語フォント（MSゴシック推奨）

## インストール方法
```bash
pip install pygame
```

## ゲームルール

### デジタル版独自のルール
**駒の表示方式**
- **自分の駒**: 種類が表示される（大将、中将、スパイなど）
- **相手の駒**: 伏せた状態で表示される（「？」マークで統一表示）
- **理由**: ネットワーク対戦では物理的に駒を裏返す必要がないため、プレイアビリティ向上のため

**従来の軍人将棋との違い**
- 従来版：両プレイヤーの駒を全て裏返して配置、お互いに駒の種類が不明
- デジタル版：自分の駒のみ表向き、相手の駒のみ伏せて表示
- この変更により戦略立案がしやすくなり、デジタル環境に最適化

ゲーム開始時にプレイヤーは自陣に駒を配置する。
**重要**: 相手プレイヤーの駒は常に伏せられた状態（マーク表示なし）で表示され、種類は不明のままゲームが進行する。
相手の駒は伏せられており種類がわからない。
駒の種類は不明のままゲームが進行する。
- **戦闘**: 駒が重なると戦闘が発生し勝敗表にしたがって負けた駒が盤面から除外される。引き分けの場合は双方の駒を除外。

### 盤面
- **変形8×6のマス目** (幅8×高さ3) x2
- **各プレイヤーは23個の駒**を使用
- **初期配置エリア**: 各プレイヤーの陣地に自由配置

### 駒の種類と数量

**23枚型ルール**

| 駒の種類 | 数量 | 分類 |
|---------|-----|------|
| 大将 | 1 | 将官 |
| 中将 | 1 | 将官 |
| 少将 | 1 | 将官 |
| 大佐 | 1 | 佐官 |
| 中佐 | 1 | 佐官 |
| 少佐 | 1 | 佐官 |
| 大尉 | 2 | 尉官 |
| 中尉 | 2 | 尉官 |
| 少尉 | 2 | 尉官 |
| 飛行機 | 2 | 特殊駒 |
| タンク | 2 | 特殊駒 |
| 騎兵 | 1 | 特殊駒 |
| 工兵 | 2 | 特殊駒 |
| スパイ | 1 | 特殊駒 |
| 地雷 | 2 | 固定駒 |
| 軍旗 | 1 | 固定駒 |

**盤面**: 変形8×6マス

自陣3x8マスと敵陣3x8マス。
自陣と敵陣の間には侵入不可領域がある。
左から2マス目と右から2マス目だけ突入口があり侵入可能。橋の上は滞在不可。

自陣の一番下(敵陣から遠い側)の中央2マスを1マスにつなげて、味方総司令部とする。
同様に敵陣の一番上の中央2マス分も敵総司令部である。総司令部内における駒は1つ。


### 駒の動かし方

#### 基本駒（将官・佐官・尉官・スパイ）
- **移動範囲**: 前後左右に1マス
- **対象**: 大将、中将、少将、大佐、中佐、少佐、大尉、中尉、少尉、スパイ

#### 特殊な移動を持つ駒

**タンク・騎兵**
- **移動範囲**: 前後左右の1マス、または2マス前
- **制限**: 手前に駒がある場合は飛び越えて2マス前に進むことはできない

**飛行機**
- **移動範囲**: 前後には何マスでも、左右は1マス
- **特殊能力**: 途中の駒を飛び越えられ、侵入不可領域を無視してどこからでも敵陣に攻め込める

**工兵**
- **移動範囲**: 前後左右に何マスでも（将棋の飛車と同じ動き）
- **制限**: 途中の駒は飛び越せない

**軍旗・地雷**
- **移動**: 動かせない（固定駒）


### 勝敗表

| 攻撃側＼防御側 | 大将 | 中将 | 少将 | 大佐 | 中佐 | 少佐 | 大尉 | 中尉 | 少尉 | 飛行機 | タンク | 騎兵 | 工兵 | スパイ | 地雷 |
|-------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-------|-------|-----|-----|-------|-----|
| **大将** | ＝ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | × | ＝ |
| **中将** | × | ＝ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ＝ |
| **少将** | × | × | ＝ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ＝ |
| **大佐** | × | × | × | ＝ | ○ | ○ | ○ | ○ | ○ | × | × | ○ | ○ | ○ | ＝ |
| **中佐** | × | × | × | × | ＝ | ○ | ○ | ○ | ○ | × | × | ○ | ○ | ○ | ＝ |
| **少佐** | × | × | × | × | × | ＝ | ○ | ○ | ○ | × | × | ○ | ○ | ○ | ＝ |
| **大尉** | × | × | × | × | × | × | ＝ | ○ | ○ | × | × | ○ | ○ | ○ | ＝ |
| **中尉** | × | × | × | × | × | × | × | ＝ | ○ | × | × | ○ | ○ | ○ | ＝ |
| **少尉** | × | × | × | × | × | × | × | × | ＝ | × | × | ○ | ○ | ○ | ＝ |
| **飛行機** | × | × | × | ○ | ○ | ○ | ○ | ○ | ○ | ＝ | ○ | ○ | ○ | ○ | ○ |
| **タンク** | × | × | × | ○ | ○ | ○ | ○ | ○ | ○ | × | ＝ | ○ | × | ○ | ＝ |
| **騎兵** | × | × | × | × | × | × | × | × | × | × | × | ＝ | ○ | ○ | ＝ |
| **工兵** | × | × | × | × | × | × | × | × | × | × | ○ | × | ＝ | ○ | ○ |
| **スパイ** | ○ | × | × | × | × | × | × | × | × | × | × | × | × | ＝ | ＝ |
| **地雷** | ＝ | ＝ | ＝ | ＝ | ＝ | ＝ | ＝ | ＝ | ＝ | × | ＝ | ＝ | × | ＝ | - |

**凡例**: ○=勝利、×=敗北、＝=相討ち


### 戦闘ルール詳細

#### 基本駒の強さ序列
**大将 > 中将 > 少将 > 大佐 > 中佐 > 少佐 > 大尉 > 中尉 > 少尉**

例：少将と中佐が戦うと少将が勝利。将官・佐官は司令部を占領できるため、尉官より価値が高い。

#### 特殊駒の戦闘ルール

**飛行機**
- 将官（大将・中将・少将）にのみ負ける
- その他の全ての駒に勝利

**タンク**
- 将官、飛行機、工兵、地雷に負ける
- その他の駒に勝利

**地雷**
- 飛行機と工兵に負ける
- その他の駒とは相討ち
- 移動不可

**工兵**
- 地雷、スパイ、タンクに勝利
- その他の駒に負ける

**騎兵**
- スパイと工兵にのみ勝利
- その他の駒に負ける

**スパイ**
- 大将にのみ勝利
- その他の駒に負ける（動ける駒の中で最弱）

**軍旗**
- すぐ後ろにある味方の駒と同じ威力を持つ
- 例：軍旗の後ろが少将の場合、軍旗はタンクに勝利
- 例：軍旗の後ろが大佐の場合、軍旗はタンクに負ける
- 軍旗の後ろが地雷の場合、タンクと軍旗は相討ち（地雷は残存）
- 軍旗の後ろが敵駒・空白・最後列の場合、全ての駒に負ける
- 移動不可


### ゲーム内の戦闘システム
- **接触戦闘**: 駒同士が隣接すると自動的に戦闘発生
- **情報隠蔽**: 戦闘後も相手の駒の種類は判明しない
- **結果表示**: 自分の駒の種類と勝敗結果のみ表示
- **戦略要素**: 相手の駒の種類を推理しながら戦う

### ゲーム内の移動システム
- **基本移動**: 将官・佐官・尉官・スパイは前後左右に1マス
- **特殊移動**: タンク・騎兵は1マスまたは2マス前、飛行機は縦横無尽、工兵は直線移動
- **移動制限**: 自分の駒がいるマスには移動不可
- **固定駒**: 軍旗・地雷は移動不可

### 勝利条件

敵の総司令部マスを大将、中将、少将、大佐、中佐、少佐のいずれかの駒で占拠する（これら以外の駒で、相手の総司令部に侵入できたとしても、占拠したことにはならない）か、動かせる駒を全滅させることが目的である。
なお、前記の駒が相手の総司令部に入った時点で占拠したとみなされるので、後からその駒を取ることはできず、ゲーム終了となる。
総司令部が占拠されれば、残った駒の種類や数に関係なくゲームの負けとなる。


### ゲームフロー
1. **駒配置フェーズ**: 各プレイヤーが自陣に駒を配置
2. **配置完了**: 両プレイヤーが配置完了ボタンを押す
3. **ゲーム開始**: プレイヤー1から交互に移動
4. **戦闘発生**: 駒が接触すると自動戦闘
5. **勝利判定**: 勝利条件を満たすまで継続

## 操作方法

### メニュー画面
- **ホストゲーム**: サーバーを立てて相手の接続を待機
- **ゲームに参加**: IPアドレスを入力してホストに接続
- **終了**: ゲーム終了

### 配置フェーズ
- **ドラッグ&ドロップ操作**: 駒置きに盤面と同じ駒が個数分表示されていて、駒をドラッグして盤面に配置
- **盤面内移動**: 盤面上で駒をドラッグして別のマスに移動
- **右クリック削除**: 盤面上の駒を右クリックで駒置きに戻す
- **自動配置ボタン**: ランダムに駒を自動配置
- **配置完了ボタン**: 配置を確定して相手を待機

### ゲームプレイ
- **駒選択**: 自分の駒をクリックして選択（駒の種類が表示される）
- **移動**: 移動可能なマス（緑色表示）をクリック
- **相手駒の識別**: 相手の駒は「？」マークで表示され種類不明
- **戦闘**: 相手の駒に隣接すると自動戦闘（戦闘後も相手駒の種類は不明のまま）
- **ESCキー**: メニューに戻る

## ネットワークプロトコル（サーバー中心型）

サーバーが唯一の権威的な盤面状態を保持し、全ての判定を行います。クライアントは操作リクエストを送信し、サーバーから盤面更新を受信するだけです。

### 基本アーキテクチャ

```
クライアント1    サーバー（ホスト）    クライアント2
    │                │                    │
    │──── 操作要求 ────→│                    │
    │                │←──── 操作要求 ───────│
    │←── 盤面更新 ─────│                    │
    │                │────── 盤面更新 ─────→│
```

**サーバーの責任**:
- 盤面状態の管理
- 移動可能性の判定
- 戦闘結果の計算
- 勝利条件の判定
- 全クライアントへの状態配信

**クライアントの責任**:
- ユーザー操作の受付
- 操作リクエストの送信
- 受信した盤面状態の表示

### 基本メッセージ構造
```json
{
    "type": "メッセージタイプ",
    "timestamp": "送信時刻",
    "data": {メッセージデータ}
}
```

### メッセージタイプ一覧

#### 1. 接続メッセージ (client_connect)
**クライアント→サーバー**
```json
{
    "type": "client_connect",
    "data": {
        "player_name": "プレイヤー名（オプション）"
    }
}
```

**サーバー→クライアント（応答）**
```json
{
    "type": "connection_accepted",
    "data": {
        "player_id": 1,
        "game_state": "waiting|setup|playing|finished",
        "message": "プレイヤー1として接続しました"
    }
}
```

#### 2. 配置リクエスト (setup_request)
**クライアント→サーバー**
```json
{
    "type": "setup_request",
    "data": {
        "action": "place|remove|auto|complete",
        "piece_type": 1,
        "position": {"x": 0, "y": 5},
        "positions": [
            {"piece_type": 1, "x": 0, "y": 5},
            {"piece_type": 2, "x": 1, "y": 5}
        ]
    }
}
```

**サーバー→全クライアント（配信）**
```json
{
    "type": "setup_update",
    "data": {
        "player": 1,
        "setup_complete": false,
        "remaining_pieces": {
            "1": 1, "2": 1, "3": 1
        },
        "visible_positions": [
            {"x": 0, "y": 5, "player": 1, "piece_type": 1},
            {"x": 1, "y": 5, "player": 1, "piece_type": null}
        ]
    }
}
```

#### 3. 移動リクエスト (move_request)
**クライアント→サーバー**
```json
{
    "type": "move_request",
    "data": {
        "from": {"x": 0, "y": 5},
        "to": {"x": 0, "y": 4}
    }
}
```

**サーバー→全クライアント（配信）**
```json
{
    "type": "game_update",
    "data": {
        "move_result": {
            "success": true,
            "from": {"x": 0, "y": 5},
            "to": {"x": 0, "y": 4},
            "battle": null
        },
        "current_player": 2,
        "board_state": [
            {
                "x": 0, "y": 4, "player": 1,
                "piece_type": 1,     // 自分の駒のみ種類表示
                "visible_to": [1]    // プレイヤー1にのみ種類が見える
            },
            {
                "x": 1, "y": 2, "player": 2,
                "piece_type": null,  // 相手の駒は種類隠蔽
                "visible_to": [2]
            }
        ]
    }
}
```

#### 4. 戦闘結果配信 (battle_result)
**サーバー→全クライアント（戦闘発生時）**
```json
{
    "type": "battle_result",
    "data": {
        "position": {"x": 1, "y": 3},
        "attacker": {
            "player": 1,
            "piece_type": 5,        // 攻撃側にのみ自分の駒種類を通知
            "visible_to": [1]
        },
        "defender": {
            "player": 2,
            "piece_type": 8,        // 守備側にのみ自分の駒種類を通知
            "visible_to": [2]
        },
        "result": "attacker_wins|defender_wins|draw",
        "survivors": [
            {"player": 1, "piece_type": 5, "visible_to": [1]}
        ]
    }
}
```

#### 5. ゲーム状態配信 (game_state)
**サーバー→全クライアント（状態変更時）**
```json
{
    "type": "game_state",
    "data": {
        "state": "setup|playing|finished",
        "current_player": 1,
        "winner": null,
        "win_reason": null,
        "setup_status": {
            "player1_complete": true,
            "player2_complete": false
        }
    }
}
```

#### 6. エラー通知 (error)
**サーバー→クライアント**
```json
{
    "type": "error",
    "data": {
        "code": "invalid_move|not_your_turn|game_not_started",
        "message": "不正な移動です",
        "details": "選択した駒は移動できません"
    }
}
```

#### 7. 切断通知 (disconnect)
**クライアント→サーバー**
```json
{
    "type": "disconnect",
    "data": {}
}
```

**サーバー→残りクライアント**
```json
{
    "type": "player_disconnected",
    "data": {
        "player": 2,
        "message": "プレイヤー2が切断しました"
    }
}
```

### 情報隠蔽の仕組み

#### プレイヤー視点別データ配信
サーバーは同じイベントを各プレイヤーに異なる内容で送信：

```json
// プレイヤー1向け
{
    "type": "game_update",
    "data": {
        "board_state": [
            {"x": 0, "y": 5, "player": 1, "piece_type": 1},      // 自分の駒：種類表示
            {"x": 0, "y": 2, "player": 2, "piece_type": null}    // 相手の駒：隠蔽
        ]
    }
}

// プレイヤー2向け
{
    "type": "game_update", 
    "data": {
        "board_state": [
            {"x": 0, "y": 5, "player": 1, "piece_type": null},   // 相手の駒：隠蔽
            {"x": 0, "y": 2, "player": 2, "piece_type": 3}       // 自分の駒：種類表示
        ]
    }
}
```

### プロトコル実装例

#### サーバー側メッセージハンドラ
```python
class GameServer:
    def handle_client_message(self, client_id, message):
        msg_type = message.get("type")
        
        if msg_type == "move_request":
            self.handle_move_request(client_id, message["data"])
        elif msg_type == "setup_request":
            self.handle_setup_request(client_id, message["data"])
        elif msg_type == "client_connect":
            self.handle_client_connect(client_id, message["data"])
            
    def broadcast_game_update(self, update_data):
        """各プレイヤーに視点別データを送信"""
        for player_id, connection in self.connections.items():
            player_view = self.create_player_specific_view(update_data, player_id)
            self.send_to_client(connection, {
                "type": "game_update",
                "data": player_view
            })
```

#### クライアント側メッセージハンドラ
```python
class GameClient:
    def handle_server_message(self, message):
        msg_type = message.get("type")
        
        if msg_type == "game_update":
            self.update_display_board(message["data"])
        elif msg_type == "battle_result":
            self.show_battle_animation(message["data"])
        elif msg_type == "error":
            self.show_error_dialog(message["data"])
            
    def send_move_request(self, from_pos, to_pos):
        """移動操作をサーバーにリクエスト"""
        request = {
            "type": "move_request",
            "data": {
                "from": {"x": from_pos[0], "y": from_pos[1]},
                "to": {"x": to_pos[0], "y": to_pos[1]}
            }
        }
        self.network.send(request)
```

### 通信の流れ（具体例）

#### 配置フェーズ
```
1. Client1: {"type": "setup_request", "data": {"action": "place", "piece_type": 1, "position": {"x": 0, "y": 5}}}
2. Server: {"type": "setup_update", "data": {"player": 1, "remaining_pieces": {...}}} → All Clients
3. Client2: {"type": "setup_request", "data": {"action": "auto"}}
4. Server: {"type": "setup_update", "data": {"player": 2, "setup_complete": true}} → All Clients
```

#### ゲームプレイフェーズ
```
1. Client1: {"type": "move_request", "data": {"from": {"x": 0, "y": 5}, "to": {"x": 0, "y": 4}}}
2. Server: 移動可能性を検証 → 盤面状態を更新
3. Server: {"type": "game_update", "data": {...}} → Client1 (自分の駒種類表示)
4. Server: {"type": "game_update", "data": {...}} → Client2 (相手の駒は隠蔽)
```

#### 戦闘発生時
```
1. Client1: {"type": "move_request", "data": {"from": {"x": 0, "y": 4}, "to": {"x": 0, "y": 3}}}
2. Server: 戦闘発生を検出 → 勝敗判定実行
3. Server: {"type": "battle_result", "data": {...}} → Client1 (攻撃側視点)
4. Server: {"type": "battle_result", "data": {...}} → Client2 (守備側視点)  
5. Server: {"type": "game_update", "data": {...}} → All Clients (戦闘後の盤面)
```

この設計により、各クライアントは単純に「操作リクエスト送信」と「受信データの表示」のみを担当し、複雑な同期処理やチート対策はすべてサーバー側で一元管理できます。

## ファイル構成
```
gunjin/
├── main.py              # エントリーポイント
├── game_client.py       # メインゲームロジック
├── game_board.py        # ゲーム盤面管理
├── pieces.py            # 駒クラス定義
├── network.py           # ネットワーク通信管理
├── ui.py                # ユーザーインターフェース
├── constants.py         # ゲーム定数
├── requirements.txt     # 依存関係
└── README.md            # このファイル
```

## 起動方法
```bash
# ゲーム開始
python main.py

# 操作手順:
# 1. メニューで「ホストゲーム」または「ゲームに参加」を選択
# 2. 駒配置画面で駒を配置
# 3. 「配置完了」ボタンでゲーム開始
# 4. 交互に駒を移動して対戦
```

## 技術仕様

### アーキテクチャ（サーバー中心型）

#### 設計思想
このゲームは **サーバー中心アーキテクチャ** を採用しています。これにより以下の利点があります：

**✅ 利点**
- **同期の簡素化**: サーバーが唯一の真実の源として機能
- **チート対策**: 全ての判定をサーバーが実行、クライアント側での改ざん防止
- **デバッグの容易さ**: 状態管理が一箇所に集中
- **拡張性**: 観戦機能やリプレイ機能の追加が容易
- **一貫性**: 同期エラーやデータの不整合が発生しない

#### データフロー
```
1. クライアント操作 → サーバーへリクエスト送信
2. サーバーで妥当性検証 → ゲーム状態更新  
3. サーバーから全クライアントへ結果配信
4. クライアントで受信データを画面に反映
```

#### 情報隠蔽戦略
サーバーは各プレイヤーに **異なる視点のデータ** を送信：
- **自分の駒**: `piece_type` フィールドに実際の駒種類
- **相手の駒**: `piece_type` フィールドは `null`（位置情報のみ）

```python
# サーバーでの視点別データ生成例
def create_player_view(board_state, viewing_player):
    player_view = []
    for piece in board_state:
        if piece.player == viewing_player:
            # 自分の駒：種類も含める
            player_view.append({
                "x": piece.x, "y": piece.y,
                "player": piece.player,
                "piece_type": piece.piece_type
            })
        else:
            # 相手の駒：種類は隠蔽
            player_view.append({
                "x": piece.x, "y": piece.y, 
                "player": piece.player,
                "piece_type": null
            })
    return player_view
```

### クライアント・サーバーモデル
- **サーバー（ホスト）**: ゲーム状態管理 + ネットワーク処理 + UI表示
- **クライアント**: UI表示 + ユーザー入力 + ネットワーク通信
- **状態同期**: サーバー → クライアント（一方向）
- **操作要求**: クライアント → サーバー（リクエスト型）

### 実装の詳細

#### サーバーサイド処理
```python
class GameServer:
    def __init__(self):
        self.board = GameBoard()           # 権威的な盤面状態
        self.players = {}                  # 接続プレイヤー管理
        self.current_player = PLAYER1      # 現在のターン
        
    def handle_move_request(self, player_id, move_data):
        # 1. 移動可能性の検証
        if not self.validate_move(player_id, move_data):
            self.send_error(player_id, "invalid_move")
            return
            
        # 2. 移動実行・戦闘判定
        result = self.board.execute_move(move_data)
        
        # 3. 全クライアントに結果配信（視点別）
        for pid, connection in self.players.items():
            player_view = self.create_player_view(pid)
            self.send_update(pid, player_view, result)
            
    def create_player_view(self, viewing_player):
        """プレイヤー視点での盤面データを生成"""
        # 自分の駒は種類表示、相手の駒は隠蔽
```

#### クライアントサイド処理  
```python
class GameClient:
    def __init__(self):
        self.display_board = GameBoard()   # 表示用盤面（読み取り専用）
        self.my_player = None              # 自分のプレイヤーID
        
    def handle_user_click(self, pos):
        # 1. UI操作をサーバーリクエストに変換
        move_request = self.create_move_request(pos)
        
        # 2. サーバーに送信（結果は非同期で受信）
        self.network.send_move_request(move_request)
        
    def handle_server_update(self, update_data):
        # 3. サーバーからの更新を表示盤面に反映
        self.display_board.update_from_server(update_data)
        self.render_board()
```

#### 戦闘システム
```python
def server_battle_resolution(attacker, defender):
    """サーバーサイドの戦闘処理"""
    # 1. 勝敗表による判定
    result = BATTLE_TABLE[attacker.type][defender.type]
    
    # 2. 結果に基づく駒の処理
    survivors = []
    if result == 1:      # 攻撃側勝利
        survivors.append(attacker)
    elif result == -1:   # 守備側勝利  
        survivors.append(defender)
    # result == 0: 相討ち（両方削除）
    
    # 3. 各プレイヤーに異なる戦闘結果を送信
    return {
        "result": result,
        "position": defender.position,
        "attacker_info": {"type": attacker.type, "visible_to": [attacker.player]},
        "defender_info": {"type": defender.type, "visible_to": [defender.player]},
        "survivors": survivors
    }
```

## トラブルシューティング

### 接続エラー
```
問題: "Connection refused" エラー
解決: 
1. ホスト側でファイアウォールを確認
2. ポート8888が開放されているか確認
3. IPアドレスが正しいか確認
```


### ゲーム同期エラー
```
問題: 駒の位置がずれる
解決:
1. 両プレイヤーでゲームを再起動
2. ネットワーク接続を確認
3. ログファイルでエラーをチェック
```

## 開発情報

### サーバー中心型実装のポイント

#### ✅ 推奨パターン
```python
# 1. クライアントは操作リクエストのみ送信
def on_piece_clicked(self, piece, target_pos):
    request = {"type": "move_request", "data": {"from": piece.pos, "to": target_pos}}
    self.network.send(request)

# 2. サーバーで全ての判定を実行
def handle_move_request(self, player, request):
    if self.validate_move(player, request):
        result = self.execute_move(request)
        self.broadcast_update(result)

# 3. クライアントは受信データをそのまま表示
def handle_server_update(self, data):
    self.board.update_from_server_data(data)
    self.refresh_display()
```

#### ❌ 避けるべきパターン
```python
# クライアントサイドでの判定（チートの温床）
if self.board.is_valid_move(from_pos, to_pos):  # ❌
    self.execute_move()

# クライアント間の直接同期（同期エラーの原因）
self.sync_board_with_other_client()  # ❌

# 部分的な状態更新（不整合の原因）
self.board.update_piece_position(piece, new_pos)  # ❌
```

#### 実装時の重要な設計原則

1. **Single Source of Truth**: サーバーのみが権威的状態を保持
2. **Request-Response Pattern**: クライアントはリクエスト、サーバーがレスポンス
3. **View Separation**: 各プレイヤーに異なる視点のデータを送信
4. **Server Validation**: 全ての操作をサーバーで検証
5. **Atomic Updates**: 状態更新は原子的操作として実行

#### デバッグとテストの簡素化

```python
# サーバーログ：全ての操作が一箇所に記録される
def log_game_event(self, event_type, data):
    print(f"[SERVER] {event_type}: {data}")
    self.game_log.append({"timestamp": time.time(), "event": event_type, "data": data})

# クライアント状態の検証
def validate_client_sync(self):
    server_state = self.request_server_state()
    client_state = self.display_board.get_state()
    assert server_state == client_state, "Client desync detected!"
```

### 従来方式との比較

| 課題 | 分散型（旧） | サーバー中心型（新） |
|------|------------|------------------|
| **同期エラー** | 頻繁に発生 | 発生しない |
| **情報漏洩** | 配置時に漏洩リスク | サーバーが制御 |
| **チート対策** | クライアント信頼ベース | サーバー検証 |
| **デバッグ** | 複数箇所の状態確認が必要 | サーバーログのみ |
| **拡張性** | 各クライアントに機能追加 | サーバーのみ機能追加 |

### 今後の拡張予定
- [ ] AI対戦機能
- [ ] リプレイ機能
- [ ] 初期配置の保存
- [ ] ランキング機能

### 既知の制限事項
- 2人以上の対戦は非対応
- リプレイ・観戦機能なし
- チャット機能なし

## ライセンス
MIT License

## 作者
Created with GitHub Copilot

## バージョン履歴
- **v1.0.0**: 初回リリース
  - 基本的なゲーム機能
  - LAN対戦機能
  - 完全隠蔽情報システム
  - リアルタイム同期
