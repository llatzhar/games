#!/usr/bin/env python3
"""戦闘システムのデバッグ用テスト"""

from game_state import Enemy, GameState


def test_battle_initiative():
    """イニシアチブ順での戦闘テスト"""
    print("=== 戦闘システムデバッグテスト ===")

    # GameStateを作成
    game_state = GameState()
    game_state.initialize_default_state()

    # 戦闘参加者を表示
    city_id = 3  # East city（初期設定でプレイヤーと敵がいる）
    players, enemies = game_state.get_characters_in_city(city_id)

    print(f"戦闘地点: {game_state.get_city_display_name(city_id)}")
    print(f"プレイヤー数: {len(players)}")
    print(f"敵数: {len(enemies)}")

    if not players or not enemies:
        print("戦闘参加者を追加...")
        # プレイヤー2をEast cityに移動
        if len(game_state.players) > 1:
            player2 = game_state.players[1]
            player2.current_city_id = city_id
            player2.x = game_state.cities[city_id].x
            player2.y = game_state.cities[city_id].y

        # 敵を追加
        enemy2 = Enemy(
            game_state.cities[city_id].x,
            game_state.cities[city_id].y,
            city_id,
            "defensive",
            2,
        )
        game_state.enemies.append(enemy2)

        # 再取得
        players, enemies = game_state.get_characters_in_city(city_id)

    print("\n戦闘参加者:")
    all_characters = players + enemies
    for i, char in enumerate(all_characters):
        char_type = "Player" if char in players else f"Enemy({char.ai_type})"
        print(
            f"  {i+1}. {char_type} - Initiative: {char.initiative}, Life: {char.life}, Attack: {char.attack}"
        )

    # イニシアチブ順をソート
    initiative_order = sorted(all_characters, key=lambda c: c.initiative, reverse=True)

    print("\nイニシアチブ順:")
    for i, char in enumerate(initiative_order):
        char_type = "Player" if char in players else f"Enemy({char.ai_type})"
        print(f"  {i+1}. {char_type} (Initiative: {char.initiative})")

    # 戦闘シミュレーション
    print("\n=== 戦闘シミュレーション開始 ===")
    round_num = 1

    for attacker in initiative_order:
        if attacker.life <= 0:
            continue

        char_type = "Player" if attacker in players else f"Enemy({attacker.ai_type})"
        print(f"\nRound {round_num}: {char_type} (Init:{attacker.initiative}) の攻撃")

        if attacker in players:
            # プレイヤーの攻撃
            alive_enemies = [e for e in enemies if e.life > 0]
            if alive_enemies:
                target = min(alive_enemies, key=lambda e: e.life)
                damage = min(attacker.attack, target.life)
                target.life = max(0, target.life - damage)
                print(
                    f"  → Enemy({target.ai_type})に{damage}ダメージ (残りHP: {target.life})"
                )
            else:
                print("  → 攻撃対象なし")
        else:
            # 敵の攻撃
            alive_players = [p for p in players if p.life > 0]
            if alive_players:
                target = min(alive_players, key=lambda p: p.life)
                damage = min(attacker.attack, target.life)
                target.life = max(0, target.life - damage)
                print(f"  → Playerに{damage}ダメージ (残りHP: {target.life})")
            else:
                print("  → 攻撃対象なし")

        round_num += 1

    print("\n=== 戦闘終了 ===")
    print("戦闘後の状態:")
    for char in all_characters:
        char_type = "Player" if char in players else f"Enemy({char.ai_type})"
        status = "生存" if char.life > 0 else "敗北"
        print(f"  {char_type}: HP {char.life}/{char.max_life} ({status})")


if __name__ == "__main__":
    test_battle_initiative()
