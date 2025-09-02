# -*- coding: utf-8 -*-
"""
軍人将棋 LAN対戦版 - メインエントリーポイント
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """メイン関数"""
    print("=" * 50)
    print("軍人将棋 LAN対戦版")
    print("=" * 50)
    print()
    print("1. クライアント（ゲーム）を起動")
    print("2. サーバーのみを起動")
    print("3. 終了")
    print()
    
    while True:
        try:
            choice = input("選択してください (1-3): ").strip()
            
            if choice == "1":
                # クライアント起動
                print("クライアントを起動します...")
                from game_client import main as client_main
                client_main()
                break
                
            elif choice == "2":
                # サーバーのみ起動
                print("サーバーのみを起動します...")
                from game_server import main as server_main
                server_main()
                break
                
            elif choice == "3":
                # 終了
                print("終了します。")
                break
                
            else:
                print("無効な選択です。1-3で選択してください。")
                
        except KeyboardInterrupt:
            print("\n終了します。")
            break
        except EOFError:
            print("\n終了します。")
            break


if __name__ == "__main__":
    main()
