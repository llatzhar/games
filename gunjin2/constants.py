# -*- coding: utf-8 -*-
"""
軍人将棋 - 定数定義
"""

# 盤面サイズ
BOARD_WIDTH = 8
BOARD_HEIGHT = 6

# プレイヤー定義
PLAYER1 = 1
PLAYER2 = 2
NO_PLAYER = 0

# 駒の種類（23枚型ルール）
PIECE_TYPES = {
    1: {"name": "大将", "count": 1, "rank": 1, "movable": True},
    2: {"name": "中将", "count": 1, "rank": 2, "movable": True}, 
    3: {"name": "少将", "count": 1, "rank": 3, "movable": True},
    4: {"name": "大佐", "count": 1, "rank": 4, "movable": True},
    5: {"name": "中佐", "count": 1, "rank": 5, "movable": True},
    6: {"name": "少佐", "count": 1, "rank": 6, "movable": True},
    7: {"name": "大尉", "count": 2, "rank": 7, "movable": True},
    8: {"name": "中尉", "count": 2, "rank": 8, "movable": True},
    9: {"name": "少尉", "count": 2, "rank": 9, "movable": True},
    10: {"name": "飛行機", "count": 2, "rank": 10, "movable": True},
    11: {"name": "タンク", "count": 2, "rank": 11, "movable": True},
    12: {"name": "騎兵", "count": 1, "rank": 12, "movable": True},
    13: {"name": "工兵", "count": 2, "rank": 13, "movable": True},
    14: {"name": "スパイ", "count": 1, "rank": 14, "movable": True},
    15: {"name": "地雷", "count": 2, "rank": 15, "movable": False},
    16: {"name": "軍旗", "count": 1, "rank": 16, "movable": False},
}

# 駒種類の逆引き
PIECE_NAMES = {v["name"]: k for k, v in PIECE_TYPES.items()}

# 司令部占拠可能な駒（将官・佐官のみ）
COMMANDER_PIECES = [1, 2, 3, 4, 5, 6]  # 大将〜少佐

# 戦闘結果定数
BATTLE_WIN = 1      # 攻撃側勝利
BATTLE_LOSE = -1    # 攻撃側敗北
BATTLE_DRAW = 0     # 相討ち

# 戦闘結果表（攻撃側 vs 防御側）
# 1: 攻撃側勝利, -1: 攻撃側敗北, 0: 相討ち
BATTLE_TABLE = {
    # 攻撃側: 大将(1)
    1: {1: 0, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: -1, 15: 0, 16: 1},
    # 攻撃側: 中将(2)  
    2: {1: -1, 2: 0, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 少将(3)
    3: {1: -1, 2: -1, 3: 0, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 大佐(4)
    4: {1: -1, 2: -1, 3: -1, 4: 0, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: -1, 11: -1, 12: 1, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 中佐(5)
    5: {1: -1, 2: -1, 3: -1, 4: -1, 5: 0, 6: 1, 7: 1, 8: 1, 9: 1, 10: -1, 11: -1, 12: 1, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 少佐(6)
    6: {1: -1, 2: -1, 3: -1, 4: -1, 5: -1, 6: 0, 7: 1, 8: 1, 9: 1, 10: -1, 11: -1, 12: 1, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 大尉(7)
    7: {1: -1, 2: -1, 3: -1, 4: -1, 5: -1, 6: -1, 7: 0, 8: 1, 9: 1, 10: -1, 11: -1, 12: 1, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 中尉(8)
    8: {1: -1, 2: -1, 3: -1, 4: -1, 5: -1, 6: -1, 7: -1, 8: 0, 9: 1, 10: -1, 11: -1, 12: 1, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 少尉(9)
    9: {1: -1, 2: -1, 3: -1, 4: -1, 5: -1, 6: -1, 7: -1, 8: -1, 9: 0, 10: -1, 11: -1, 12: 1, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 飛行機(10)
    10: {1: -1, 2: -1, 3: -1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 0, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1},
    # 攻撃側: タンク(11)
    11: {1: -1, 2: -1, 3: -1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: -1, 11: 0, 12: 1, 13: -1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 騎兵(12)
    12: {1: -1, 2: -1, 3: -1, 4: -1, 5: -1, 6: -1, 7: -1, 8: -1, 9: -1, 10: -1, 11: -1, 12: 0, 13: 1, 14: 1, 15: 0, 16: 1},
    # 攻撃側: 工兵(13)
    13: {1: -1, 2: -1, 3: -1, 4: -1, 5: -1, 6: -1, 7: -1, 8: -1, 9: -1, 10: -1, 11: 1, 12: -1, 13: 0, 14: 1, 15: 1, 16: 1},
    # 攻撃側: スパイ(14)
    14: {1: 1, 2: -1, 3: -1, 4: -1, 5: -1, 6: -1, 7: -1, 8: -1, 9: -1, 10: -1, 11: -1, 12: -1, 13: -1, 14: 0, 15: 0, 16: 1},
    # 攻撃側: 地雷(15) - 移動不可なので攻撃側にはならない
    15: {},
    # 攻撃側: 軍旗(16) - 移動不可なので攻撃側にはならない
    16: {}
}

# ゲーム状態
GAME_STATE_WAITING = "waiting"      # プレイヤー接続待ち
GAME_STATE_SETUP = "setup"          # 駒配置フェーズ
GAME_STATE_PLAYING = "playing"      # ゲームプレイ中
GAME_STATE_FINISHED = "finished"    # ゲーム終了

# 勝利理由
WIN_REASON_HEADQUARTERS = "headquarters"    # 司令部占拠
WIN_REASON_ELIMINATION = "elimination"      # 相手全滅
WIN_REASON_DISCONNECT = "disconnect"        # 相手切断

# ネットワーク設定
DEFAULT_HOST = "0.0.0.0"  # すべてのインターフェースでリッスン
DEFAULT_PORT = 8888
MAX_CONNECTIONS = 2

# UI設定
CELL_SIZE = 60
BOARD_MARGIN = 50
PIECE_FONT_SIZE = 16
UI_FONT_SIZE = 20
TITLE_FONT_SIZE = 24

# 色定義（RGB）
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_LIGHT_GRAY = (192, 192, 192)
COLOR_DARK_GRAY = (64, 64, 64)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_BROWN = (139, 69, 19)
COLOR_ORANGE = (255, 165, 0)

# プレイヤー色
PLAYER1_COLOR = COLOR_RED
PLAYER2_COLOR = COLOR_BLUE
SELECTED_COLOR = COLOR_GREEN
VALID_MOVE_COLOR = (144, 238, 144)  # Light Green
ENEMY_PIECE_COLOR = COLOR_GRAY

# 盤面定義
# プレイヤー1の初期配置エリア（下側）
PLAYER1_SETUP_AREA = [(x, y) for x in range(BOARD_WIDTH) for y in range(3, BOARD_HEIGHT)]
# プレイヤー2の初期配置エリア（上側）  
PLAYER2_SETUP_AREA = [(x, y) for x in range(BOARD_WIDTH) for y in range(0, 3)]

# 司令部の位置
# プレイヤー1の司令部（下側中央）
PLAYER1_HEADQUARTERS = [(3, 5)] # , (4, 5)]
# プレイヤー2の司令部（上側中央）
PLAYER2_HEADQUARTERS = [(3, 0)] # , (4, 0)]

# 侵入不可領域と突入口
NEUTRAL_ZONE_HEIGHT = 1
NEUTRAL_ZONE_Y = 3  # 中央線
BRIDGE_POSITIONS = [(1, 3), (6, 3)]  # 突入口の位置

# メッセージタイプ
MSG_CLIENT_CONNECT = "client_connect"
MSG_CONNECTION_ACCEPTED = "connection_accepted"
MSG_SETUP_REQUEST = "setup_request"
MSG_SETUP_UPDATE = "setup_update"
MSG_MOVE_REQUEST = "move_request"
MSG_GAME_UPDATE = "game_update"
MSG_BATTLE_RESULT = "battle_result"
MSG_GAME_STATE = "game_state"
MSG_ERROR = "error"
MSG_DISCONNECT = "disconnect"
MSG_PLAYER_DISCONNECTED = "player_disconnected"

# エラーコード
ERROR_INVALID_MOVE = "invalid_move"
ERROR_NOT_YOUR_TURN = "not_your_turn"
ERROR_GAME_NOT_STARTED = "game_not_started"
ERROR_CONNECTION_FULL = "connection_full"
ERROR_SETUP_NOT_COMPLETE = "setup_not_complete"
