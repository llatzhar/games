from abc import ABC, abstractmethod
from enum import Enum
import pyxel

class MapStateType(Enum):
    """マップシーンの状態タイプ"""
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    TRANSITION = "transition"
    BATTLE_SEQUENCE = "battle_sequence"
    CUTIN = "cutin"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    PAUSED = "paused"

class MapGameState(ABC):
    """マップゲーム状態の基底クラス"""
    
    def __init__(self, context, state_type: MapStateType):
        self.context = context  # MapSceneへの参照
        self.state_type = state_type
        self.enter_time = 0  # 状態に入った時間
    
    @abstractmethod
    def enter(self):
        """状態開始時の処理"""
        self.enter_time = pyxel.frame_count
        
    @abstractmethod
    def update(self):
        """毎フレーム更新処理
        Returns:
            Scene: 継続する場合はself、シーン変更の場合は新しいシーン、終了の場合はNone
        """
        pass
    
    @abstractmethod
    def handle_input(self):
        """入力処理"""
        pass
    
    @abstractmethod
    def exit(self):
        """状態終了時の処理"""
        pass
    
    def transition_to(self, new_state):
        """状態遷移実行"""
        self.context.change_state(new_state)
    
    def get_elapsed_time(self):
        """状態に入ってからの経過時間（フレーム数）"""
        return pyxel.frame_count - self.enter_time

class StateContext:
    """状態管理コンテキスト"""
    
    def __init__(self):
        self.current_state = None
        self.previous_state = None
        self.state_history = []  # デバッグ用状態履歴
        
    def change_state(self, new_state):
        """状態を変更"""
        if self.current_state:
            self.current_state.exit()
            self.previous_state = self.current_state
            
        # 状態履歴を記録（最新10件まで）
        if len(self.state_history) >= 10:
            self.state_history.pop(0)
        self.state_history.append({
            'from': self.current_state.state_type if self.current_state else None,
            'to': new_state.state_type,
            'time': pyxel.frame_count
        })
        
        self.current_state = new_state
        new_state.enter()
    
    def update(self):
        """現在の状態を更新"""
        if self.current_state:
            return self.current_state.update()
        return None
    
    def handle_input(self):
        """現在の状態の入力処理"""
        if self.current_state:
            self.current_state.handle_input()
    
    def get_current_state_type(self):
        """現在の状態タイプを取得"""
        return self.current_state.state_type if self.current_state else None
    
    def draw_debug_info(self, x, y):
        """デバッグ情報を描画"""
        if self.current_state:
            current_type = self.current_state.state_type.value
            elapsed = self.current_state.get_elapsed_time()
            pyxel.text(x, y, f"State: {current_type} ({elapsed}f)", 7)
            
            # 状態履歴を表示
            for i, history in enumerate(self.state_history[-3:]):  # 最新3件
                from_state = history['from'].value if history['from'] else "None"
                to_state = history['to'].value
                pyxel.text(x, y + 10 + i * 8, f"  {from_state} -> {to_state}", 6)
