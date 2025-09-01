"""
ゲーム定数定義
"""

# 盤面サイズ（8x6）
BOARD_WIDTH = 8
BOARD_HEIGHT = 6

# プレイヤー
PLAYER_1 = 1
PLAYER_2 = 2

# ゲーム状態
GAME_STATE_MENU = "menu"
GAME_STATE_WAITING = "waiting"
GAME_STATE_SETUP = "setup"
GAME_STATE_PLAYING = "playing"
GAME_STATE_GAME_OVER = "game_over"

# 駒の種類（16種類、合計23個）
PIECE_GENERAL = "大将"           # 1個 - 将官
PIECE_LT_GENERAL = "中将"        # 1個 - 将官
PIECE_MAJ_GENERAL = "少将"       # 1個 - 将官
PIECE_COLONEL = "大佐"           # 1個 - 佐官
PIECE_LT_COLONEL = "中佐"        # 1個 - 佐官
PIECE_MAJOR = "少佐"             # 1個 - 佐官
PIECE_CAPTAIN = "大尉"           # 2個 - 尉官
PIECE_LT = "中尉"                # 2個 - 尉官
PIECE_2ND_LT = "少尉"           # 2個 - 尉官
PIECE_AIRCRAFT = "飛行機"        # 2個 - 特殊駒
PIECE_TANK = "タンク"            # 2個 - 特殊駒
PIECE_CAVALRY = "騎兵"           # 1個 - 特殊駒
PIECE_ENGINEER = "工兵"          # 2個 - 特殊駒
PIECE_SPY = "スパイ"             # 1個 - 特殊駒
PIECE_MINE = "地雷"              # 2個 - 固定駒
PIECE_FLAG = "軍旗"              # 1個 - 固定駒

# 駒名表示用辞書
PIECE_NAMES = {
    PIECE_GENERAL: "大将",
    PIECE_LT_GENERAL: "中将",
    PIECE_MAJ_GENERAL: "少将",
    PIECE_COLONEL: "大佐",
    PIECE_LT_COLONEL: "中佐",
    PIECE_MAJOR: "少佐",
    PIECE_CAPTAIN: "大尉",
    PIECE_LT: "中尉",
    PIECE_2ND_LT: "少尉",
    PIECE_AIRCRAFT: "飛行機",
    PIECE_TANK: "タンク",
    PIECE_CAVALRY: "騎兵",
    PIECE_ENGINEER: "工兵",
    PIECE_SPY: "スパイ",
    PIECE_MINE: "地雷",
    PIECE_FLAG: "軍旗"
}

# 指揮駒（総司令部占領に必要）
COMMAND_PIECES = [PIECE_GENERAL, PIECE_LT_GENERAL, PIECE_MAJ_GENERAL, 
                  PIECE_COLONEL, PIECE_LT_COLONEL, PIECE_MAJOR]

# 移動不可能な駒（固定駒）
IMMOVABLE_PIECES = [PIECE_MINE, PIECE_FLAG]

# 初期駒構成（READMEの23枚型ルール）
INITIAL_PIECE_COUNTS = {
    PIECE_GENERAL: 1,      # 大将
    PIECE_LT_GENERAL: 1,   # 中将
    PIECE_MAJ_GENERAL: 1,  # 少将
    PIECE_COLONEL: 1,      # 大佐
    PIECE_LT_COLONEL: 1,   # 中佐
    PIECE_MAJOR: 1,        # 少佐
    PIECE_CAPTAIN: 2,      # 大尉
    PIECE_LT: 2,           # 中尉
    PIECE_2ND_LT: 2,       # 少尉
    PIECE_AIRCRAFT: 2,     # 飛行機
    PIECE_TANK: 2,         # タンク
    PIECE_CAVALRY: 1,      # 騎兵
    PIECE_ENGINEER: 2,     # 工兵
    PIECE_SPY: 1,          # スパイ
    PIECE_MINE: 2,         # 地雷
    PIECE_FLAG: 1          # 軍旗
}

# ネットワーク設定
DEFAULT_PORT = 12345
MAX_CONNECTIONS = 1
BUFFER_SIZE = 1024

# UI設定
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 700
CELL_SIZE = 70
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 50

# フォントサイズ
FONT_SIZE_SMALL = 12
FONT_SIZE_MEDIUM = 16
FONT_SIZE_LARGE = 24

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BROWN = (245, 222, 179)
DARK_BROWN = (139, 69, 19)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
