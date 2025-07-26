import pyxel
import random
from map_state_machine import MapGameState, MapStateType
from cutin import CutinSubScene
from battle import BattleSubScene
from game import screen_width, screen_height

class PlayerTurnState(MapGameState):
    """プレイヤーが操作可能な状態"""
    
    def __init__(self, context):
        super().__init__(context, MapStateType.PLAYER_TURN)
        
    def enter(self):
        super().enter()
        self.context.game_state.current_turn = "player"
        self.context.game_state.player_moved_this_turn = False
        self.context.selected_player = None
        self.context.clear_camera_follow()
        
    def update(self):
        # プレイヤーの移動処理
        for player in self.context.game_state.players:
            if player.is_moving and player.target_x is not None and player.target_y is not None:
                # 移動処理
                dx = player.target_x - player.x
                dy = player.target_y - player.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                # 移動方向に基づいて向きを更新
                if abs(dx) > 1:
                    player.facing_right = dx > 0
                
                if distance <= player.speed:
                    # 目標地点に到達
                    player.x = player.target_x
                    player.y = player.target_y
                    player.current_city_id = player.target_city_id
                    player.is_moving = False
                    player.target_x = None
                    player.target_y = None
                    player.target_city_id = None
                    # プレイヤーの移動完了時にTransitionStateに遷移
                    self.transition_to(TransitionState(self.context))
                    return self.context
                else:
                    # 目標地点に向かって移動
                    player.x += (dx / distance) * player.speed
                    player.y += (dy / distance) * player.speed
        
        return self.context
    
    def handle_input(self):
        # ターンスキップ
        if pyxel.btnp(pyxel.KEY_SPACE):
            if not any(player.is_moving for player in self.context.game_state.players):
                self.transition_to(TransitionState(self.context))
                return
        
        # マウスクリック処理
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.context.click_x = pyxel.mouse_x
            self.context.click_y = pyxel.mouse_y
            self.context.click_timer = 120
            
            if self.context.can_move_this_turn():
                clicked_player = self.context.get_player_at_position(self.context.click_x, self.context.click_y)
                clicked_city = self.context.get_city_at_position(self.context.click_x, self.context.click_y)
                
                if clicked_player:
                    # プレイヤーを選択
                    self.context.selected_player = clicked_player
                elif clicked_city and self.context.selected_player:
                    # プレイヤーの移動処理
                    current_city = self.context.get_player_current_city(self.context.selected_player)
                    
                    if current_city and self.context.is_cities_connected(current_city, clicked_city):
                        # 接続されているCityにのみ移動可能
                        clicked_city_id = clicked_city.id
                        self.context.selected_player.target_x = clicked_city.x
                        self.context.selected_player.target_y = clicked_city.y
                        self.context.selected_player.target_city_id = clicked_city_id
                        self.context.selected_player.is_moving = True
                        self.context.game_state.player_moved_this_turn = True
                        self.context.game_state.auto_save()
        
        # ESCキーで選択解除
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.context.selected_player = None
    
    def exit(self):
        pass

class EnemyTurnState(MapGameState):
    """AIが自動実行される状態"""
    
    def __init__(self, context):
        super().__init__(context, MapStateType.ENEMY_TURN)
        
    def enter(self):
        super().enter()
        self.context.game_state.current_turn = "enemy"
        self.context.game_state.enemy_moved_this_turn = False
        self.context.selected_enemy = None
        self.context.game_state.ai_timer = 0
        self.context.clear_camera_follow()
        
    def update(self):
        # 敵の移動処理
        for enemy in self.context.game_state.enemies:
            if enemy.is_moving and enemy.target_x is not None and enemy.target_y is not None:
                # 移動処理
                dx = enemy.target_x - enemy.x
                dy = enemy.target_y - enemy.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                # 移動方向に基づいて向きを更新
                if abs(dx) > 1:
                    enemy.facing_right = dx > 0
                
                if distance <= enemy.speed:
                    # 目標地点に到達
                    enemy.x = enemy.target_x
                    enemy.y = enemy.target_y
                    enemy.current_city_id = enemy.target_city_id
                    enemy.is_moving = False
                    enemy.target_x = None
                    enemy.target_y = None
                    enemy.target_city_id = None
                    # 敵の移動完了時にTransitionStateに遷移
                    self.transition_to(TransitionState(self.context))
                    return self.context
                else:
                    # 目標地点に向かって移動
                    enemy.x += (dx / distance) * enemy.speed
                    enemy.y += (dy / distance) * enemy.speed
        
        # AI処理
        if self.context.can_move_this_turn():
            if not any(enemy.is_moving for enemy in self.context.game_state.enemies):
                self.context.game_state.ai_timer += 1
                
                if self.context.game_state.ai_timer >= self.context.game_state.ai_decision_delay:
                    self.context.execute_enemy_ai_turn()
                    self.context.game_state.ai_timer = 0
        
        return self.context
    
    def handle_input(self):
        # ターンスキップ
        if pyxel.btnp(pyxel.KEY_SPACE):
            if not any(enemy.is_moving for enemy in self.context.game_state.enemies):
                self.transition_to(TransitionState(self.context))
                return
        
        # 敵の手動選択（デバッグ用）
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.context.click_x = pyxel.mouse_x
            self.context.click_y = pyxel.mouse_y
            self.context.click_timer = 120
            
            if self.context.can_move_this_turn():
                clicked_enemy = self.context.get_enemy_at_position(self.context.click_x, self.context.click_y)
                clicked_city = self.context.get_city_at_position(self.context.click_x, self.context.click_y)
                
                if clicked_enemy:
                    self.context.selected_enemy = clicked_enemy
                    self.context.set_camera_follow_target(clicked_enemy)
                elif clicked_city and self.context.selected_enemy:
                    # 敵の移動処理
                    current_city = self.context.game_state.get_city_by_id(self.context.selected_enemy.current_city_id) if self.context.selected_enemy.current_city_id else None
                    
                    if current_city and self.context.is_cities_connected(current_city, clicked_city):
                        clicked_city_id = clicked_city.id
                        self.context.selected_enemy.target_x = clicked_city.x
                        self.context.selected_enemy.target_y = clicked_city.y
                        self.context.selected_enemy.target_city_id = clicked_city_id
                        self.context.selected_enemy.is_moving = True
                        self.context.game_state.enemy_moved_this_turn = True
                        self.context.game_state.auto_save()
        
        # ESCキーで選択解除
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.context.selected_enemy = None
    
    def exit(self):
        pass

class TransitionState(MapGameState):
    """ターン間の遷移処理状態"""
    
    def __init__(self, context):
        super().__init__(context, MapStateType.TRANSITION)
        
    def enter(self):
        super().enter()
        # 戦闘チェック
        self.battle_locations = self.context.game_state.check_battles()
        
        # 次のターンを決定
        if self.context.game_state.current_turn == "player":
            self.next_turn = "enemy"
        else:
            self.next_turn = "player"
            self.context.game_state.turn_counter += 1
        
        # 自動セーブ
        self.context.game_state.auto_save()
        
    def update(self):
        # ゲーム終了条件チェック
        if not self.context.game_state.players:
            self.transition_to(GameOverState(self.context, is_victory=False))
            return self.context
        elif not self.context.game_state.enemies:
            self.transition_to(GameOverState(self.context, is_victory=True))
            return self.context
        
        # 戦闘がある場合
        if self.battle_locations:
            self.transition_to(BattleSequenceState(self.context, self.battle_locations))
            return self.context
        
        # 戦闘がない場合はカットイン状態へ
        if self.next_turn == "player":
            cutin_text = "PLAYER TURN"
        else:
            cutin_text = "ENEMY TURN"
        self.transition_to(CutinState(self.context, cutin_text, self.next_turn))
        return self.context
    
    def handle_input(self):
        # この状態では入力を受け付けない
        pass
    
    def exit(self):
        pass

class BattleSequenceState(MapGameState):
    """複数戦闘の連続処理状態"""
    
    def __init__(self, context, battle_locations):
        super().__init__(context, MapStateType.BATTLE_SEQUENCE)
        self.battle_locations = battle_locations
        self.current_battle_index = 0
        self.camera_moving = False
        self.camera_timer = 0
        
    def enter(self):
        super().enter()
        self.context.is_processing_battles = True
        self.start_next_battle()
        
    def update(self):
        # カメラ移動待機中
        if self.camera_moving:
            self.camera_timer -= 1
            if self.camera_timer <= 0:
                self.camera_moving = False
                # BattleSubSceneを開始
                self.start_battle_scene()
        
        return self.context
        
    def start_next_battle(self):
        """次の戦闘を開始"""
        if self.current_battle_index < len(self.battle_locations):
            current_battle = self.battle_locations[self.current_battle_index]
            city_id = current_battle['city_id']
            city = self.context.game_state.get_city_by_id(city_id)
            
            if city:
                # 戦闘都市にカメラを移動
                self.context.move_camera_to_city(city)
                self.camera_moving = True
                self.camera_timer = 60  # 2秒待機
        else:
            # 全戦闘完了
            self.finish_battles()
    
    def start_battle_scene(self):
        """現在の戦闘のBattleSubSceneを開始"""
        current_battle = self.battle_locations[self.current_battle_index]
        city_id = current_battle['city_id']
        city = self.context.game_state.get_city_by_id(city_id)
        
        if city:
            battle_sub_scene = BattleSubScene(self.context, current_battle, city)
            self.context.set_sub_scene(battle_sub_scene)
    
    def on_battle_finished(self):
        """戦闘終了時の処理"""
        self.current_battle_index += 1
        if self.current_battle_index < len(self.battle_locations):
            self.start_next_battle()
        else:
            self.finish_battles()
    
    def finish_battles(self):
        """全戦闘完了時の処理"""
        self.context.game_state.remove_defeated_characters()
        
        # 次のターンのカットインへ遷移
        if self.context.game_state.current_turn == "player":
            cutin_text = "ENEMY TURN"
            next_turn = "enemy"
        else:
            cutin_text = "PLAYER TURN"
            next_turn = "player"
            
        self.transition_to(CutinState(self.context, cutin_text, next_turn))
    
    def handle_input(self):
        # 戦闘中は基本的に入力を受け付けない（Qキーでの終了のみ）
        pass
    
    def exit(self):
        self.context.is_processing_battles = False

class CutinState(MapGameState):
    """カットイン演出状態"""
    
    def __init__(self, context, cutin_text, next_turn):
        super().__init__(context, MapStateType.CUTIN)
        self.cutin_text = cutin_text
        self.next_turn = next_turn
        
    def enter(self):
        super().enter()
        cutin_sub_scene = CutinSubScene(self.context, self.cutin_text)
        self.context.set_sub_scene(cutin_sub_scene)
        
    def update(self):
        # CutinSubSceneが終了したら次のターンへ
        if not self.context.sub_scene:
            if self.next_turn == "player":
                self.transition_to(PlayerTurnState(self.context))
            else:
                self.transition_to(EnemyTurnState(self.context))
        
        return self.context
    
    def handle_input(self):
        # カットイン中は入力を受け付けない
        pass
    
    def exit(self):
        pass

class GameOverState(MapGameState):
    """ゲーム終了状態"""
    
    def __init__(self, context, is_victory=False):
        state_type = MapStateType.VICTORY if is_victory else MapStateType.GAME_OVER
        super().__init__(context, state_type)
        self.is_victory = is_victory
        
    def enter(self):
        super().enter()
        
    def update(self):
        return self.context
    
    def handle_input(self):
        # Qキーでタイトルに戻る
        if pyxel.btnp(pyxel.KEY_Q):
            from game import TitleScene
            # 新しいシーンを返すために、コンテキストに通知
            self.context.next_scene = TitleScene()
    
    def draw_overlay(self):
        """ゲーム終了画面のオーバーレイを描画"""
        if self.is_victory:
            pyxel.text(screen_width // 2 - 20, screen_height // 2, "VICTORY!", 11)
        else:
            pyxel.text(screen_width // 2 - 30, screen_height // 2, "GAME OVER", 8)
        pyxel.text(screen_width // 2 - 40, screen_height // 2 + 10, "Press Q to return to title", 7)
    
    def exit(self):
        pass

class PausedState(MapGameState):
    """一時停止状態"""
    
    def __init__(self, context, previous_state):
        super().__init__(context, MapStateType.PAUSED)
        self.previous_state = previous_state
        
    def enter(self):
        super().enter()
        
    def update(self):
        return self.context
    
    def handle_input(self):
        # ESCキーで前の状態に復帰
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.transition_to(self.previous_state)
    
    def exit(self):
        pass
