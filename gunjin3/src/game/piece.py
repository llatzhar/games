from enum import Enum, auto

class Rank(Enum):
    # Special
    FLAG = 0      # 軍旗
    SPY = 1       # スパイ
    TANK = 2      # タンク
    PLANE = 3     # 飛行機
    
    # Officers
    MARSHAL = 15  # 大将
    GENERAL = 14  # 中将
    LT_GEN = 13   # 少将
    COLONEL = 12  # 大佐
    LT_COL = 11   # 中佐
    MAJOR = 10    # 少佐
    CAPTAIN = 9   # 大尉
    LIEUTENANT = 8 # 中尉
    SEC_LT = 7    # 少尉
    
    # Soldiers
    ENGINEER = 6  # 工兵
    CAVALRY = 5   # 騎兵
    INFANTRY = 4  # 歩兵
    
    # Other
    MINE = 99     # 地雷

class Side(Enum):
    FRONT = auto() # 手前側 (先手/Player 1)
    BACK = auto()  # 奥側 (後手/Player 2)

class Piece:
    def __init__(self, rank: Rank, side: Side):
        self.rank = rank
        self.side = side
        self.is_revealed = False

    def __repr__(self):
        return f"<{self.side.name}:{self.rank.name}>"

    @property
    def name(self):
        return self.rank.name
