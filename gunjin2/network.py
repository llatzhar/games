# -*- coding: utf-8 -*-
"""
軍人将棋 - ネットワーク通信管理
"""

import socket
import threading
import json
import time
from constants import *

class NetworkManager:
    """ネットワーク通信の基本クラス"""
    
    def __init__(self):
        self.socket = None
        self.is_connected = False
        self.message_handlers = {}
        self.receive_thread = None
        self.running = False
        
    def register_handler(self, message_type, handler):
        """メッセージハンドラを登録"""
        self.message_handlers[message_type] = handler
        
    def send_message(self, message):
        """メッセージを送信"""
        if not self.is_connected or self.socket is None:
            return False
            
        try:
            # タイムスタンプを追加
            message["timestamp"] = time.time()
            
            # デバッグ用：メッセージの内容をチェック
            try:
                message_json = json.dumps(message, ensure_ascii=False)
            except TypeError as e:
                print(f"JSONシリアライズエラー詳細: {e}")
                print(f"問題のメッセージタイプ: {message.get('type', 'unknown')}")
                print(f"メッセージ内容: {str(message)[:200]}...")
                return False
                
            message_bytes = message_json.encode('utf-8')
            message_length = len(message_bytes)
            
            # メッセージ長を先に送信（4バイト）
            self.socket.send(message_length.to_bytes(4, byteorder='big'))
            # メッセージ本体を送信
            self.socket.send(message_bytes)
            return True
            
        except Exception as e:
            print(f"メッセージ送信エラー: {e}")
            self.disconnect()
            return False
            
    def _receive_message(self):
        """メッセージを受信（内部メソッド）"""
        try:
            # メッセージ長を受信（4バイト）
            length_bytes = self._receive_exact(4)
            if not length_bytes:
                return None
                
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            # メッセージ本体を受信
            message_bytes = self._receive_exact(message_length)
            if not message_bytes:
                return None
                
            message_json = message_bytes.decode('utf-8')
            return json.loads(message_json)
            
        except Exception as e:
            print(f"メッセージ受信エラー: {e}")
            return None
            
    def _receive_exact(self, length):
        """指定バイト数を確実に受信"""
        data = b''
        while len(data) < length:
            try:
                chunk = self.socket.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            except Exception as e:
                print(f"データ受信エラー: {e}")
                return None
        return data
        
    def _receive_loop(self):
        """メッセージ受信ループ"""
        while self.running and self.is_connected:
            message = self._receive_message()
            if message is None:
                break
                
            # メッセージハンドラを呼び出し
            message_type = message.get("type")
            if message_type in self.message_handlers:
                try:
                    self.message_handlers[message_type](message)
                except Exception as e:
                    print(f"メッセージハンドラエラー ({message_type}): {e}")
                    
        self.disconnect()
        
    def disconnect(self):
        """接続を切断"""
        self.running = False
        self.is_connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        if self.receive_thread and self.receive_thread.is_alive():
            if self.receive_thread != threading.current_thread():
                self.receive_thread.join(timeout=1.0)


class GameServer(NetworkManager):
    """ゲームサーバー"""
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        super().__init__()
        self.host = host
        self.port = port
        self.server_socket = None
        self.connections = {}  # client_id -> connection
        self.client_counter = 0
        self.accept_thread = None
        
    def start_server(self):
        """サーバー開始"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(MAX_CONNECTIONS)
            
            self.running = True
            self.accept_thread = threading.Thread(target=self._accept_loop)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            print(f"サーバー開始: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"サーバー開始エラー: {e}")
            return False
            
    def _accept_loop(self):
        """クライアント接続受付ループ"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                
                # 最大接続数チェック
                if len(self.connections) >= MAX_CONNECTIONS:
                    # 接続拒否
                    error_message = {
                        "type": MSG_ERROR,
                        "data": {
                            "code": ERROR_CONNECTION_FULL,
                            "message": "サーバーが満員です"
                        }
                    }
                    self._send_to_socket(client_socket, error_message)
                    client_socket.close()
                    continue
                    
                # クライアント登録
                client_id = self.client_counter + 1
                self.client_counter += 1
                
                connection = ClientConnection(client_id, client_socket, client_address)
                self.connections[client_id] = connection
                
                # クライアント受信スレッド開始
                receive_thread = threading.Thread(
                    target=self._client_receive_loop,
                    args=(client_id, connection)
                )
                receive_thread.daemon = True
                receive_thread.start()
                
                print(f"クライアント接続: {client_address} (ID: {client_id})")
                
                # 接続確認メッセージを送信
                self._handle_client_connect(client_id, {})
                
            except Exception as e:
                if self.running:
                    print(f"クライアント接続エラー: {e}")
                break
                
    def _client_receive_loop(self, client_id, connection):
        """クライアントメッセージ受信ループ"""
        while self.running and client_id in self.connections:
            try:
                message = self._receive_from_connection(connection)
                if message is None:
                    break
                    
                # メッセージハンドラを呼び出し
                message_type = message.get("type")
                if message_type in self.message_handlers:
                    try:
                        self.message_handlers[message_type](client_id, message)
                    except Exception as e:
                        print(f"クライアントメッセージハンドラエラー ({message_type}): {e}")
                        
            except Exception as e:
                print(f"クライアント受信エラー (ID: {client_id}): {e}")
                break
                
        # クライアント切断処理
        self._handle_client_disconnect(client_id)
        
    def _receive_from_connection(self, connection):
        """接続からメッセージを受信"""
        try:
            # メッセージ長を受信
            length_bytes = self._receive_exact_from_socket(connection.socket, 4)
            if not length_bytes:
                return None
                
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            # メッセージ本体を受信
            message_bytes = self._receive_exact_from_socket(connection.socket, message_length)
            if not message_bytes:
                return None
                
            message_json = message_bytes.decode('utf-8')
            return json.loads(message_json)
            
        except Exception as e:
            print(f"接続からの受信エラー: {e}")
            return None
            
    def _receive_exact_from_socket(self, sock, length):
        """ソケットから指定バイト数を確実に受信"""
        data = b''
        while len(data) < length:
            try:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            except Exception as e:
                return None
        return data
        
    def send_to_client(self, client_id, message):
        """特定クライアントにメッセージ送信"""
        if client_id not in self.connections:
            return False
            
        connection = self.connections[client_id]
        return self._send_to_socket(connection.socket, message)
        
    def broadcast_message(self, message, exclude_client=None):
        """全クライアントにメッセージをブロードキャスト"""
        for client_id, connection in list(self.connections.items()):
            if exclude_client is None or client_id != exclude_client:
                if not self._send_to_socket(connection.socket, message):
                    # 送信失敗したクライアントを切断
                    self._handle_client_disconnect(client_id)
                    
    def _send_to_socket(self, sock, message):
        """ソケットにメッセージ送信"""
        try:
            # タイムスタンプを追加
            message["timestamp"] = time.time()
            
            # デバッグ用：メッセージの内容をチェック
            try:
                message_json = json.dumps(message, ensure_ascii=False)
            except TypeError as e:
                print(f"サーバー側JSONシリアライズエラー詳細: {e}")
                print(f"問題のメッセージタイプ: {message.get('type', 'unknown')}")
                print(f"メッセージ内容: {str(message)[:300]}...")
                return False
                
            message_bytes = message_json.encode('utf-8')
            message_length = len(message_bytes)
            
            sock.send(message_length.to_bytes(4, byteorder='big'))
            sock.send(message_bytes)
            return True
            
        except Exception as e:
            print(f"ソケット送信エラー: {e}")
            return False
            
    def _handle_client_connect(self, client_id, message_data):
        """クライアント接続処理"""
        # プレイヤーIDを割り当て
        player_id = PLAYER1 if len(self.connections) == 1 else PLAYER2
        
        connection = self.connections[client_id]
        connection.player_id = player_id
        
        # 接続受諾応答
        response = {
            "type": MSG_CONNECTION_ACCEPTED,
            "data": {
                "player_id": player_id,
                "game_state": GAME_STATE_WAITING,
                "message": f"プレイヤー{player_id}として接続しました"
            }
        }
        self.send_to_client(client_id, response)
        
    def _handle_client_disconnect(self, client_id):
        """クライアント切断処理"""
        if client_id not in self.connections:
            return
            
        connection = self.connections[client_id]
        player_id = getattr(connection, 'player_id', None)
        
        # 接続を削除
        try:
            connection.socket.close()
        except:
            pass
        del self.connections[client_id]
        
        print(f"クライアント切断: ID {client_id}")
        
        # 他のクライアントに切断を通知
        if player_id is not None:
            disconnect_message = {
                "type": MSG_PLAYER_DISCONNECTED,
                "data": {
                    "player": player_id,
                    "message": f"プレイヤー{player_id}が切断しました"
                }
            }
            self.broadcast_message(disconnect_message)
            
    def stop_server(self):
        """サーバー停止"""
        self.running = False
        
        # 全クライアント切断
        for client_id in list(self.connections.keys()):
            self._handle_client_disconnect(client_id)
            
        # サーバーソケット閉鎖
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        print("サーバー停止")


class GameClient(NetworkManager):
    """ゲームクライアント"""
    
    def __init__(self):
        super().__init__()
        self.player_id = None
        
    def connect_to_server(self, host, port):
        """サーバーに接続"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            
            self.is_connected = True
            self.running = True
            
            # 受信スレッド開始
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # 接続メッセージを送信
            connect_message = {
                "type": MSG_CLIENT_CONNECT,
                "data": {}
            }
            self.send_message(connect_message)
            
            print(f"サーバーに接続: {host}:{port}")
            return True
            
        except Exception as e:
            print(f"サーバー接続エラー: {e}")
            self.disconnect()
            return False


class ClientConnection:
    """クライアント接続情報"""
    
    def __init__(self, client_id, socket, address):
        self.client_id = client_id
        self.socket = socket
        self.address = address
        self.player_id = None
        self.connected_time = time.time()


def create_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """サーバーインスタンスを作成"""
    return GameServer(host, port)


def create_client():
    """クライアントインスタンスを作成"""
    return GameClient()
