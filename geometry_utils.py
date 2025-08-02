"""
幾何学的計算のためのユーティリティ関数
"""


def line_intersects_line(x1, y1, x2, y2, x3, y3, x4, y4):
    """2つの線分が交差するかチェック
    
    Args:
        x1, y1: 線分1の開始点
        x2, y2: 線分1の終了点
        x3, y3: 線分2の開始点
        x4, y4: 線分2の終了点
    
    Returns:
        bool: 線分が交差する場合True
    """

    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)

    return ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and ccw(
        x1, y1, x2, y2, x3, y3
    ) != ccw(x1, y1, x2, y2, x4, y4)


def roads_intersect(road1_start, road1_end, road2_start, road2_end):
    """2つの道路が交差するかチェック
    
    Args:
        road1_start: (x, y) 道路1の開始点
        road1_end: (x, y) 道路1の終了点
        road2_start: (x, y) 道路2の開始点
        road2_end: (x, y) 道路2の終了点
    
    Returns:
        bool: 道路が交差する場合True
    """
    x1, y1 = road1_start
    x2, y2 = road1_end
    x3, y3 = road2_start
    x4, y4 = road2_end
    
    return line_intersects_line(x1, y1, x2, y2, x3, y3, x4, y4)


def point_too_close_to_line(point_x, point_y, line_start, line_end, min_distance=10):
    """点が線分に近すぎるかチェック
    
    Args:
        point_x, point_y: チェックする点の座標
        line_start: (x, y) 線分の開始点
        line_end: (x, y) 線分の終了点
        min_distance: 最小距離（ピクセル）
    
    Returns:
        bool: 点が線分に近すぎる場合True
    """
    x1, y1 = line_start
    x2, y2 = line_end
    
    # 線分の長さの二乗
    line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
    
    if line_length_sq == 0:
        # 線分が点の場合、点間の距離をチェック
        distance_sq = (point_x - x1) ** 2 + (point_y - y1) ** 2
        return distance_sq < min_distance ** 2
    
    # 点から線分への最短距離を計算
    t = max(0, min(1, ((point_x - x1) * (x2 - x1) + (point_y - y1) * (y2 - y1)) / line_length_sq))
    
    # 線分上の最も近い点
    closest_x = x1 + t * (x2 - x1)
    closest_y = y1 + t * (y2 - y1)
    
    # 点と最も近い点の距離の二乗
    distance_sq = (point_x - closest_x) ** 2 + (point_y - closest_y) ** 2
    
    return distance_sq < min_distance ** 2
