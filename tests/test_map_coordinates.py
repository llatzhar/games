import os
import sys
import unittest

# テストファイルからプロジェクトルートのモジュールをインポートできるようにする
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from coordinate_utils import (  # noqa: E402
    CoordinateTransformer,
    create_default_coordinate_transformer,
)
from game_state import GameState  # noqa: E402


class TestCoordinateTransformer(unittest.TestCase):
    """CoordinateTransformerの座標変換テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.transformer = create_default_coordinate_transformer()

    def test_coordinate_transformer_constants(self):
        """CoordinateTransformerの定数テスト"""
        self.assertEqual(self.transformer.tile_size, 32)
        self.assertEqual(self.transformer.tile_offset_x, 8)
        self.assertEqual(self.transformer.tile_offset_y, 8)
        self.assertEqual(self.transformer.map_width, 17)
        self.assertEqual(self.transformer.map_height, 17)

    def test_tile_to_pixel_conversion(self):
        """タイル→ピクセル変換テスト"""
        # 中央（タイル座標0,0）→ 物理座標(256,256)
        pixel_x, pixel_y = self.transformer.tile_to_pixel(0, 0)
        self.assertEqual(pixel_x, 256.0)
        self.assertEqual(pixel_y, 256.0)

        # 左上端（タイル座標-8,-8）→ 物理座標(0,0)
        pixel_x, pixel_y = self.transformer.tile_to_pixel(-8, -8)
        self.assertEqual(pixel_x, 0.0)
        self.assertEqual(pixel_y, 0.0)

        # 右下端（タイル座標8,8）→ 物理座標(512,512)
        pixel_x, pixel_y = self.transformer.tile_to_pixel(8, 8)
        self.assertEqual(pixel_x, 512.0)
        self.assertEqual(pixel_y, 512.0)

        # 任意の座標（タイル座標-1,2）→ 物理座標(224,320)
        pixel_x, pixel_y = self.transformer.tile_to_pixel(-1, 2)
        self.assertEqual(pixel_x, 224.0)
        self.assertEqual(pixel_y, 320.0)

    def test_pixel_to_tile_conversion(self):
        """ピクセル→タイル変換テスト"""
        # 物理座標(256,256) → タイル座標(0,0)
        tile_x, tile_y = self.transformer.pixel_to_tile(256.0, 256.0)
        self.assertEqual(tile_x, 0)
        self.assertEqual(tile_y, 0)

        # 物理座標(0,0) → タイル座標(-8,-8)
        tile_x, tile_y = self.transformer.pixel_to_tile(0.0, 0.0)
        self.assertEqual(tile_x, -8)
        self.assertEqual(tile_y, -8)

        # 物理座標(512,512) → タイル座標(8,8)
        tile_x, tile_y = self.transformer.pixel_to_tile(512.0, 512.0)
        self.assertEqual(tile_x, 8)
        self.assertEqual(tile_y, 8)

        # 任意の座標 物理座標(224,320) → タイル座標(-1,2)
        tile_x, tile_y = self.transformer.pixel_to_tile(224.0, 320.0)
        self.assertEqual(tile_x, -1)
        self.assertEqual(tile_y, 2)

    def test_coordinate_conversion_roundtrip(self):
        """座標変換の往復テスト"""
        test_coordinates = [
            (0, 0),  # 中央
            (-8, -8),  # 左上端
            (8, 8),  # 右下端
            (-4, 3),  # 任意の負座標
            (5, -2),  # 任意の混合座標
            (-1, 2),  # West都市の座標
            (1, 2),  # East都市の座標
        ]

        for original_tile_x, original_tile_y in test_coordinates:
            # タイル → ピクセル → タイル
            pixel_x, pixel_y = self.transformer.tile_to_pixel(
                original_tile_x, original_tile_y
            )
            converted_tile_x, converted_tile_y = self.transformer.pixel_to_tile(
                pixel_x, pixel_y
            )

            self.assertEqual(
                converted_tile_x,
                original_tile_x,
                f"X座標の往復変換エラー: {original_tile_x} → {pixel_x} → {converted_tile_x}",
            )
            self.assertEqual(
                converted_tile_y,
                original_tile_y,
                f"Y座標の往復変換エラー: {original_tile_y} → {pixel_y} → {converted_tile_y}",
            )

    def test_tile_to_map_index_conversion(self):
        """タイル座標→マップ配列インデックス変換テスト"""
        # 中央（タイル座標0,0）→ マップインデックス(8,8)
        map_col, map_row = self.transformer.tile_to_map_index(0, 0)
        self.assertEqual(map_col, 8)
        self.assertEqual(map_row, 8)

        # 左上端（タイル座標-8,-8）→ マップインデックス(0,0)
        map_col, map_row = self.transformer.tile_to_map_index(-8, -8)
        self.assertEqual(map_col, 0)
        self.assertEqual(map_row, 0)

        # 右下端（タイル座標8,8）→ マップインデックス(16,16)
        map_col, map_row = self.transformer.tile_to_map_index(8, 8)
        self.assertEqual(map_col, 16)
        self.assertEqual(map_row, 16)

    def test_map_index_to_tile_conversion(self):
        """マップ配列インデックス→タイル座標変換テスト"""
        # マップインデックス(8,8) → タイル座標(0,0)
        tile_x, tile_y = self.transformer.map_index_to_tile(8, 8)
        self.assertEqual(tile_x, 0)
        self.assertEqual(tile_y, 0)

        # マップインデックス(0,0) → タイル座標(-8,-8)
        tile_x, tile_y = self.transformer.map_index_to_tile(0, 0)
        self.assertEqual(tile_x, -8)
        self.assertEqual(tile_y, -8)

        # マップインデックス(16,16) → タイル座標(8,8)
        tile_x, tile_y = self.transformer.map_index_to_tile(16, 16)
        self.assertEqual(tile_x, 8)
        self.assertEqual(tile_y, 8)

    def test_coordinate_boundary_validation(self):
        """座標系境界の検証テスト"""
        # 有効な範囲内の座標テスト
        for tile_x in range(-8, 9):  # -8から8まで
            for tile_y in range(-8, 9):
                # 有効性チェック
                self.assertTrue(
                    self.transformer.is_valid_tile_coordinate(tile_x, tile_y)
                )

                # ピクセル変換
                pixel_x, pixel_y = self.transformer.tile_to_pixel(tile_x, tile_y)

                # ピクセル座標が期待される範囲内にあることを確認
                self.assertGreaterEqual(pixel_x, 0.0)
                self.assertLessEqual(pixel_x, 512.0)
                self.assertGreaterEqual(pixel_y, 0.0)
                self.assertLessEqual(pixel_y, 512.0)

                # マップインデックス変換と有効性チェック
                map_col, map_row = self.transformer.tile_to_map_index(tile_x, tile_y)
                self.assertTrue(self.transformer.is_valid_map_index(map_col, map_row))
                self.assertGreaterEqual(map_col, 0)
                self.assertLess(map_col, 17)
                self.assertGreaterEqual(map_row, 0)
                self.assertLess(map_row, 17)

        # 無効な座標のテスト
        invalid_coordinates = [(-9, 0), (9, 0), (0, -9), (0, 9), (-10, -10), (10, 10)]
        for tile_x, tile_y in invalid_coordinates:
            self.assertFalse(self.transformer.is_valid_tile_coordinate(tile_x, tile_y))

    def test_coordinate_consistency_with_game_state(self):
        """GameStateとCoordinateTransformerの座標一貫性テスト"""
        game_state = GameState()
        game_state.initialize_default_state()

        # 各都市の座標がCoordinateTransformerの変換関数と一致することを確認
        city_tile_coords = {
            1: (0, 0),  # Central
            2: (-1, 2),  # West
            3: (1, 2),  # East
        }

        for city_id, (expected_tile_x, expected_tile_y) in city_tile_coords.items():
            city = game_state.cities[city_id]

            # CoordinateTransformerの変換関数で計算した座標と一致することを確認
            expected_pixel_x, expected_pixel_y = self.transformer.tile_to_pixel(
                expected_tile_x, expected_tile_y
            )

            self.assertEqual(
                city.x,
                expected_pixel_x,
                f"都市{city.name}のX座標が不一致: 期待値{expected_pixel_x}, 実際値{city.x}",
            )
            self.assertEqual(
                city.y,
                expected_pixel_y,
                f"都市{city.name}のY座標が不一致: 期待値{expected_pixel_y}, 実際値{city.y}",
            )


class TestCoordinateTransformerEdgeCases(unittest.TestCase):
    """CoordinateTransformerのエッジケーステスト"""

    def setUp(self):
        """テスト前の準備"""
        self.transformer = create_default_coordinate_transformer()

    def test_different_map_sizes(self):
        """異なるマップサイズでの座標変換テスト"""
        # 9x9マップ（-4〜4）
        transformer_9x9 = CoordinateTransformer(tile_size=32, map_width=9, map_height=9)
        self.assertEqual(transformer_9x9.tile_offset_x, 4)
        self.assertEqual(transformer_9x9.tile_offset_y, 4)

        # 中央座標テスト
        pixel_x, pixel_y = transformer_9x9.tile_to_pixel(0, 0)
        self.assertEqual(pixel_x, 128.0)  # 4 * 32
        self.assertEqual(pixel_y, 128.0)

        # 境界テスト
        self.assertTrue(transformer_9x9.is_valid_tile_coordinate(-4, -4))
        self.assertTrue(transformer_9x9.is_valid_tile_coordinate(4, 4))
        self.assertFalse(transformer_9x9.is_valid_tile_coordinate(-5, 0))
        self.assertFalse(transformer_9x9.is_valid_tile_coordinate(5, 0))

    def test_different_tile_sizes(self):
        """異なるタイルサイズでの座標変換テスト"""
        # 16x16ピクセルタイル
        transformer_16 = CoordinateTransformer(
            tile_size=16, map_width=17, map_height=17
        )

        # 中央座標テスト
        pixel_x, pixel_y = transformer_16.tile_to_pixel(0, 0)
        self.assertEqual(pixel_x, 128.0)  # 8 * 16
        self.assertEqual(pixel_y, 128.0)

        # 64x64ピクセルタイル
        transformer_64 = CoordinateTransformer(
            tile_size=64, map_width=17, map_height=17
        )

        # 中央座標テスト
        pixel_x, pixel_y = transformer_64.tile_to_pixel(0, 0)
        self.assertEqual(pixel_x, 512.0)  # 8 * 64
        self.assertEqual(pixel_y, 512.0)

    def test_precision_handling(self):
        """精度処理のテスト"""
        # 小数点を含むピクセル座標からタイル座標への変換
        test_cases = [
            (
                255.9,
                255.9,
                -1,
                -1,
            ),  # 境界より少し小さい値 (255.9 // 32 = 7, 7 - 8 = -1)
            (256.0, 256.0, 0, 0),  # 正確な境界値 (256.0 // 32 = 8, 8 - 8 = 0)
            (256.1, 256.1, 0, 0),  # 境界より少し大きい値 (256.1 // 32 = 8, 8 - 8 = 0)
            (
                287.9,
                287.9,
                0,
                0,
            ),  # 次のタイルより少し小さい値 (287.9 // 32 = 8, 8 - 8 = 0)
            (288.0, 288.0, 1, 1),  # 次のタイルの境界値 (288.0 // 32 = 9, 9 - 8 = 1)
        ]

        for pixel_x, pixel_y, expected_tile_x, expected_tile_y in test_cases:
            tile_x, tile_y = self.transformer.pixel_to_tile(pixel_x, pixel_y)
            self.assertEqual(
                tile_x,
                expected_tile_x,
                f"ピクセル({pixel_x}, {pixel_y})のタイルX変換エラー: "
                f"期待値{expected_tile_x}, 実際値{tile_x}",
            )
            self.assertEqual(
                tile_y,
                expected_tile_y,
                f"ピクセル({pixel_x}, {pixel_y})のタイルY変換エラー: "
                f"期待値{expected_tile_y}, 実際値{tile_y}",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
