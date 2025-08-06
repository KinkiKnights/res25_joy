#!/usr/bin/env python3
"""
Enhanced HTTP Server for res25_joy directory
Optimized for handling 10MB+ file transfers
"""

import http.server
import socketserver
import os
import sys
import logging
import time
from pathlib import Path
from urllib.parse import urlparse, unquote

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    # 大きなファイル転送用の設定
    protocol_version = 'HTTP/1.1'
    
    def __init__(self, *args, **kwargs):
        # バッファサイズを増加（10MBファイル対応）
        self.buffer_size = 1024 * 1024  # 1MBバッファ
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def setup(self):
        # ソケットタイムアウトを設定（大きなファイル転送用）
        self.request.settimeout(300)  # 5分タイムアウト
        super().setup()
    
    def end_headers(self):
        # CORSヘッダーを追加
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Content-Length, Range')
        self.send_header('Access-Control-Expose-Headers', 'Content-Length, Content-Range')
        # 大きなファイル転送用のヘッダー
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()
    
    def log_message(self, format, *args):
        # 詳細なログメッセージ
        message = format % args
        logger.info(f"{self.address_string()} - {message}")
    
    def do_GET(self):
        try:
            # ファイルサイズを事前にチェック
            file_path = self.translate_path(self.path)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"ファイル要求: {self.path} (サイズ: {file_size / (1024*1024):.2f}MB)")
                
                # 大きなファイルの場合は特別な処理
                if file_size > 5 * 1024 * 1024:  # 5MB以上
                    logger.info(f"大きなファイル転送開始: {self.path}")
            
            super().do_GET()
            
        except Exception as e:
            logger.error(f"GET リクエストエラー: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def do_POST(self):
        """ファイルアップロード対応"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            logger.info(f"POST リクエスト: {self.path} (サイズ: {content_length / (1024*1024):.2f}MB)")
            
            if content_length > 50 * 1024 * 1024:  # 50MB制限
                self.send_error(413, "File too large")
                return
            
            # ファイル保存処理
            filename = unquote(self.path.lstrip('/'))
            if not filename:
                filename = f"upload_{int(time.time())}.bin"
            
            file_path = os.path.join(os.getcwd(), filename)
            
            with open(file_path, 'wb') as f:
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(self.buffer_size, remaining)
                    chunk = self.rfile.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            
            logger.info(f"ファイル保存完了: {filename}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"status": "success", "filename": "{filename}"}}'.encode())
            
        except Exception as e:
            logger.error(f"POST リクエストエラー: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def do_OPTIONS(self):
        """CORS preflight リクエスト対応"""
        self.send_response(200)
        self.end_headers()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """マルチスレッド対応HTTPサーバー"""
    allow_reuse_address = True
    daemon_threads = True
    
    def __init__(self, server_address, RequestHandlerClass):
        # 同時接続数を制限
        self.request_queue_size = 100
        super().__init__(server_address, RequestHandlerClass)

def get_system_info():
    """システム情報を取得"""
    import platform
    import psutil
    
    info = {
        'platform': platform.platform(),
        'python_version': sys.version,
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total / (1024**3),  # GB
        'disk_usage': psutil.disk_usage('.').free / (1024**3)  # GB
    }
    return info

def main():
    # ポート番号を設定（デフォルト: 8000）
    PORT = 8000
    
    # コマンドライン引数からポート番号を取得
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except ValueError:
            print(f"無効なポート番号: {sys.argv[1]}")
            sys.exit(1)
    
    # 現在のディレクトリを確認
    current_dir = os.getcwd()
    print(f"サーバーのルートディレクトリ: {current_dir}")
    
    # システム情報を表示
    try:
        system_info = get_system_info()
        print(f"\nシステム情報:")
        print(f"  プラットフォーム: {system_info['platform']}")
        print(f"  Python: {system_info['python_version']}")
        print(f"  CPU: {system_info['cpu_count']} コア")
        print(f"  メモリ: {system_info['memory_total']:.1f}GB")
        print(f"  ディスク空き容量: {system_info['disk_usage']:.1f}GB")
    except ImportError:
        print("psutilがインストールされていません。システム情報の表示をスキップします。")
    
    # 利用可能なファイルを表示
    print("\n利用可能なファイル:")
    total_size = 0
    for file in os.listdir(current_dir):
        if os.path.isfile(file):
            file_size = os.path.getsize(file)
            total_size += file_size
            size_mb = file_size / (1024*1024)
            print(f"  - {file} ({size_mb:.2f}MB)")
    
    print(f"\n合計ファイルサイズ: {total_size / (1024*1024):.2f}MB")
    
    # HTTPサーバーを作成
    try:
        with ThreadedHTTPServer(("", PORT), EnhancedHTTPRequestHandler) as httpd:
            print(f"\n🚀 サーバーを起動しました!")
            print(f"📡 URL: http://localhost:{PORT}")
            print(f"📄 index.html: http://localhost:{PORT}/index.html")
            print(f"🎮 joy.html: http://localhost:{PORT}/joy.html")
            print(f"📁 ファイルアップロード: POST http://localhost:{PORT}/filename")
            print(f"⚙️  設定:")
            print(f"   - バッファサイズ: {EnhancedHTTPRequestHandler.buffer_size / (1024*1024):.1f}MB")
            print(f"   - タイムアウト: 300秒")
            print(f"   - 最大ファイルサイズ: 50MB")
            print(f"   - 同時接続数: 100")
            print(f"\n📝 ログファイル: server.log")
            print(f"\n🛑 サーバーを停止するには Ctrl+C を押してください")
            
            logger.info(f"サーバー起動: ポート {PORT}")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しました")
        logger.info("サーバー停止")
    except Exception as e:
        print(f"\n❌ サーバー起動エラー: {e}")
        logger.error(f"サーバー起動エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 