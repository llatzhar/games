"""
ネットワーク通信管理
"""

import socket
import json
import threading
import time
from constants import *

class NetworkManager:
    """ネットワーク管理クラス"""
    
    def __init__(self, is_host=False, host_ip="localhost"):
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = DEFAULT_PORT
        self.socket = None
        self.client_socket = None
        self.running = False
        self.message_handlers = {}
        self.message_queue = []
        self.queue_lock = threading.Lock()
        
    def start_server(self):
        """サーバーを開始"""
        if not self.is_host:
            return False
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host_ip, self.port))
            self.socket.listen(MAX_CONNECTIONS)
            self.running = True
            
            print(f"サーバー開始: {self.host_ip}:{self.port}")
            
            threading.Thread(target=self._wait_for_client, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"サーバー開始エラー: {e}")
            return False
    
    def connect_to_server(self, server_ip):
        """サーバーに接続"""
        if self.is_host:
            return False
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_ip, self.port))
            self.running = True
            
            print(f"サーバーに接続: {server_ip}:{self.port}")
            
            threading.Thread(target=self._receive_messages, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"接続エラー: {e}")
            return False
    
    def _wait_for_client(self):
        """クライアント接続待機"""
        try:
            self.client_socket, addr = self.socket.accept()
            print(f"クライアント接続: {addr}")
            
            threading.Thread(target=self._receive_messages, daemon=True).start()
            
        except Exception as e:
            print(f"クライアント接続エラー: {e}")
    
    def _receive_messages(self):
        """メッセージ受信ループ"""
        active_socket = self.client_socket if self.is_host else self.socket
        
        while self.running and active_socket:
            try:
                data = active_socket.recv(BUFFER_SIZE).decode('utf-8')
                if not data:
                    break
                
                messages = data.split('\n')
                for msg in messages:
                    if msg.strip():
                        try:
                            message = json.loads(msg.strip())
                            self._handle_message(message)
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                print(f"メッセージ受信エラー: {e}")
                break
        
        self.disconnect()
    
    def _handle_message(self, message):
        """受信メッセージの処理"""
        msg_type = message.get('type')
        
        with self.queue_lock:
            self.message_queue.append(message)
        
        if msg_type in self.message_handlers:
            self.message_handlers[msg_type](message)
    
    def send_message(self, message):
        """メッセージ送信"""
        if not self.running:
            return False
        
        try:
            active_socket = self.client_socket if self.is_host else self.socket
            if active_socket:
                data = json.dumps(message, ensure_ascii=False) + '\n'
                active_socket.send(data.encode('utf-8'))
                return True
                
        except Exception as e:
            print(f"メッセージ送信エラー: {e}")
            
        return False
    
    def get_messages(self):
        """キューからメッセージを取得"""
        with self.queue_lock:
            messages = self.message_queue[:]
            self.message_queue.clear()
            return messages
    
    def register_handler(self, msg_type, handler):
        """メッセージハンドラーを登録"""
        self.message_handlers[msg_type] = handler
    
    def disconnect(self):
        """接続を切断"""
        self.running = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("ネットワーク接続を切断しました")
    
    def is_connected(self):
        """接続状態をチェック"""
        return self.running and (
            (self.is_host and self.client_socket) or 
            (not self.is_host and self.socket)
        )

class GameProtocol:
    """ゲーム通信プロトコル"""
    
    @staticmethod
    def setup_complete(player):
        """セットアップ完了メッセージ"""
        return {
            'type': 'setup_complete',
            'player': player
        }
    
    @staticmethod
    def setup_positions(player, positions):
        """セットアップ時の駒配置情報"""
        return {
            'type': 'setup_positions',
            'player': player,
            'positions': positions
        }
    
    @staticmethod
    def move(from_pos, to_pos, player, piece_type=None):
        """移動メッセージ"""
        message = {
            'type': 'move',
            'from': from_pos,
            'to': to_pos,
            'player': player
        }
        if piece_type:
            message['piece_type'] = piece_type
        return message
    
    @staticmethod
    def battle_result(attacker_pos, defender_pos, result, survivor_pos=None):
        """戦闘結果メッセージ"""
        message = {
            'type': 'battle_result',
            'attacker_pos': attacker_pos,
            'defender_pos': defender_pos,
            'result': result
        }
        if survivor_pos:
            message['survivor_pos'] = survivor_pos
        return message
    
    @staticmethod
    def reveal_piece(position, piece_type, player):
        """駒の種類開示メッセージ（戦闘時等）"""
        return {
            'type': 'reveal_piece',
            'position': position,
            'piece_type': piece_type,
            'player': player
        }
    
    @staticmethod
    def battle_info(attacker_pos, attacker_type, defender_pos, defender_type, result):
        """戦闘情報メッセージ（詳細）"""
        return {
            'type': 'battle_info',
            'attacker_pos': attacker_pos,
            'attacker_type': attacker_type,
            'defender_pos': defender_pos,
            'defender_type': defender_type,
            'result': result
        }
    
    @staticmethod
    def game_start():
        """ゲーム開始メッセージ"""
        return {
            'type': 'game_start'
        }
    
    @staticmethod
    def game_over(winner):
        """ゲーム終了メッセージ"""
        return {
            'type': 'game_over',
            'winner': winner
        }
