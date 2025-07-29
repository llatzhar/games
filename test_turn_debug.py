#!/usr/bin/env python3
"""ターン切り替えのデバッグ用テスト"""

from game_state import GameState

def test_turn_switching():
    """ターン切り替えのテスト"""
    print("=== ターン切り替えテスト ===")
    
    # GameStateを作成
    game_state = GameState()
    game_state.initialize_default_state()
    
    print(f"初期ターン: {game_state.current_turn}")
    print(f"ターンカウンター: {game_state.turn_counter}")
    
    # 複数回ターンを切り替え
    for i in range(5):
        print(f"\n--- ターン切り替え {i+1} ---")
        game_state.switch_turn()
        print(f"現在のターン: {game_state.current_turn}")
        print(f"ターンカウンター: {game_state.turn_counter}")
        print(f"プレイヤー移動済み: {game_state.player_moved_this_turn}")
        print(f"敵移動済み: {game_state.enemy_moved_this_turn}")

    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_turn_switching()
