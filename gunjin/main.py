"""
軍人将棋 LAN対戦ゲーム
エントリーポイント
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
        
        print("軍人将棋 LAN対戦を開始します...")
        client = GameClient()
        
        # メニュー画面から開始
        client.run()
        
    except ImportError as e:
        print(f"モジュールのインポートエラー: {e}")
        print("必要なファイルが不足している可能性があります")
        return 1
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        return 1
    finally:
        # pygame終了処理
        try:
            pygame.quit()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nゲームが中断されました")
        sys.exit(0)
