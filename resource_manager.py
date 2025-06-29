import pyxel

def create_resources():
    """新しいリソースファイルを作成"""
    # 画像バンクを初期化
    pyxel.init(160, 120)
    
    # 画像を描画（例：シンプルなキャラクター）
    pyxel.cls(0)
    
    # キャラクターの描画例（16x16）
    # フレーム1
    pyxel.rect(0, 0, 16, 16, 7)  # 背景
    pyxel.rect(4, 4, 8, 8, 8)    # 顔
    pyxel.pget(6, 6)             # 目
    pyxel.pget(10, 6)            # 目
    pyxel.rect(6, 10, 4, 2, 2)   # 口
    
    # フレーム2（少し違うアニメーション）
    pyxel.rect(16, 0, 16, 16, 7) # 背景
    pyxel.rect(20, 4, 8, 8, 8)   # 顔
    pyxel.pget(22, 6)            # 目
    pyxel.pget(26, 6)            # 目
    pyxel.rect(22, 10, 4, 1, 2)  # 口（小さく）
    
    # リソースファイルを保存
    pyxel.save("resources.pyxres")
    print("リソースファイルを作成しました: resources.pyxres")

def inspect_resources():
    """リソースファイルの内容を確認"""
    try:
        pyxel.init(160, 120)
        pyxel.load("resources.pyxres")
        
        print("リソースファイルの情報:")
        print("- 画像バンク0が読み込まれました")
        print("- サイズ: 256x256 (Pyxel標準)")
        
        # 特定のピクセルの色を確認
        for y in range(16):
            row = ""
            for x in range(32):  # 2フレーム分
                color = pyxel.pget(x, y)
                row += str(color)
            print(f"Row {y:2d}: {row}")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    print("1. リソース作成")
    print("2. リソース確認")
    choice = input("選択してください (1/2): ")
    
    if choice == "1":
        create_resources()
    elif choice == "2":
        inspect_resources()
