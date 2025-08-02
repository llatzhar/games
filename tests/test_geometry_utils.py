import os
import sys
import unittest

# テストファイルからプロジェクトルートのモジュールをインポートできるようにする
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from geometry_utils import line_intersects_line, roads_intersect, point_too_close_to_line  # noqa: E402


class TestGeometryUtils(unittest.TestCase):
    """geometry_utilsのテスト"""

    def test_line_intersects_line_basic(self):
        """基本的な線分交差テスト"""
        # 交差するケース：十字型
        self.assertTrue(line_intersects_line(0, 0, 10, 10, 0, 10, 10, 0))
        
        # 交差しないケース：平行線
        self.assertFalse(line_intersects_line(0, 0, 10, 0, 0, 5, 10, 5))
        
        # 交差しないケース：同じ方向
        self.assertFalse(line_intersects_line(0, 0, 5, 0, 6, 0, 10, 0))

    def test_line_intersects_line_edge_cases(self):
        """線分交差のエッジケーステスト"""
        # 端点で接触
        self.assertFalse(line_intersects_line(0, 0, 5, 0, 5, 0, 10, 0))
        
        # 同一線分
        self.assertFalse(line_intersects_line(0, 0, 10, 10, 0, 0, 10, 10))
        
        # 点と線分
        self.assertFalse(line_intersects_line(0, 0, 0, 0, 1, 1, 2, 2))

    def test_roads_intersect(self):
        """道路交差テスト"""
        road1_start = (0, 0)
        road1_end = (10, 10)
        road2_start = (0, 10)
        road2_end = (10, 0)
        
        # 交差する道路
        self.assertTrue(roads_intersect(road1_start, road1_end, road2_start, road2_end))
        
        # 交差しない道路
        road3_start = (0, 0)
        road3_end = (5, 0)
        road4_start = (6, 0)
        road4_end = (10, 0)
        
        self.assertFalse(roads_intersect(road3_start, road3_end, road4_start, road4_end))

    def test_point_too_close_to_line(self):
        """点と線分の距離テスト"""
        line_start = (0, 0)
        line_end = (10, 0)
        
        # 線分に近い点
        self.assertTrue(point_too_close_to_line(5, 2, line_start, line_end, min_distance=5))
        
        # 線分から遠い点
        self.assertFalse(point_too_close_to_line(5, 10, line_start, line_end, min_distance=5))
        
        # 線分上の点
        self.assertTrue(point_too_close_to_line(5, 0, line_start, line_end, min_distance=1))

    def test_point_too_close_to_line_edge_cases(self):
        """点と線分の距離テストのエッジケース"""
        # 線分が点の場合
        point_line_start = (5, 5)
        point_line_end = (5, 5)
        
        self.assertTrue(point_too_close_to_line(5, 5, point_line_start, point_line_end, min_distance=1))
        self.assertFalse(point_too_close_to_line(10, 10, point_line_start, point_line_end, min_distance=1))
        
        # 線分の端点近くの点
        line_start = (0, 0)
        line_end = (10, 0)
        
        # 端点の外側
        self.assertTrue(point_too_close_to_line(-1, 0, line_start, line_end, min_distance=2))
        self.assertTrue(point_too_close_to_line(11, 0, line_start, line_end, min_distance=2))


if __name__ == "__main__":
    unittest.main()
