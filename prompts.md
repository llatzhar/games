```
ゲーム用フレームワークのpyxelをつかいます。game.pyを作成して。update, drawを含んだsceneクラスを定義し、シーンごとにsceneのサブクラスをつかうようにします。
```
```
キャラクタを２パターンのアニメーションしたい。左上の16x16と、その右となりの16x16を交互に表示する。
```
```
キーボードのwasdで上下左右に動けるようにして
```
```
キャラクタが左に移動しているときは、リソースの画像をそのまま、右に移動しているときはリソースの画像を左右反転して表示して
```

pycacheをignoreする.gitignoreを追加して

ImportError: cannot import name 'MapScene' from partially initialized module 'map' (most likely due to a circular import) (C:\gits\games\map.py)

TitleSceneでEnterを押したらmapシーンに遷移するように

あたらしくmap.pyを作成して、MapScheneを定義して


マウスカーソルの表示を消さない設定にして

MapSceneでマウスクリックしたら、クリック位置の座標を表示するようにしたい