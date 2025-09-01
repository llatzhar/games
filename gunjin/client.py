"""
クライアント用エントリーポイント
"""

import sys
import os
import pygame

# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """メイン関数"""
    try:
        # pygame初期化
        pygame.init()
        
        # ゲームクライアントをインポートして起動
        from game_client import GameClient
        
        print("軍人将棋 LAN対戦（クライアント）を開始します...")
        client = GameClient()
        
        # クライアントとして開始
        client.join_game()
        client.run()
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
