"""
座標変換ユーティリティ関数
"""


class CoordinateTransformer:
    """座標変換を行うユーティリティクラス"""

    def __init__(self, tile_size: int = 32, map_width: int = 17, map_height: int = 17):
        self.tile_size = tile_size
        self.map_width = map_width
        self.map_height = map_height
        # 中央座標系のオフセット（17x17マップの場合、中央は8,8）
        self.tile_offset_x = map_width // 2
        self.tile_offset_y = map_height // 2

    def tile_to_pixel(self, tile_x: int, tile_y: int) -> tuple[float, float]:
        """タイル座標をピクセル座標に変換（中央座標系対応）"""
        pixel_x = (tile_x + self.tile_offset_x) * self.tile_size
        pixel_y = (tile_y + self.tile_offset_y) * self.tile_size
        return (pixel_x, pixel_y)

    def pixel_to_tile(self, pixel_x: float, pixel_y: float) -> tuple[int, int]:
        """ピクセル座標をタイル座標に変換（中央座標系対応）"""
        tile_x = int(pixel_x // self.tile_size) - self.tile_offset_x
        tile_y = int(pixel_y // self.tile_size) - self.tile_offset_y
        return (tile_x, tile_y)

    def tile_to_map_index(self, tile_x: int, tile_y: int) -> tuple[int, int]:
        """タイル座標をマップ配列インデックスに変換"""
        map_col = tile_x + self.tile_offset_x
        map_row = tile_y + self.tile_offset_y
        return (map_col, map_row)

    def map_index_to_tile(self, map_col: int, map_row: int) -> tuple[int, int]:
        """マップ配列インデックスをタイル座標に変換"""
        tile_x = map_col - self.tile_offset_x
        tile_y = map_row - self.tile_offset_y
        return (tile_x, tile_y)

    def is_valid_tile_coordinate(self, tile_x: int, tile_y: int) -> bool:
        """タイル座標が有効範囲内かチェック"""
        half_size = self.map_width // 2
        return -half_size <= tile_x <= half_size and -half_size <= tile_y <= half_size

    def is_valid_map_index(self, map_col: int, map_row: int) -> bool:
        """マップ配列インデックスが有効範囲内かチェック"""
        return 0 <= map_col < self.map_width and 0 <= map_row < self.map_height


def create_default_coordinate_transformer() -> CoordinateTransformer:
    """デフォルト設定の座標変換器を作成"""
    return CoordinateTransformer(tile_size=32, map_width=17, map_height=17)
