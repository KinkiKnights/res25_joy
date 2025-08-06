"""
Server Configuration
"""

# サーバー基本設定
SERVER_CONFIG = {
    'host': '0.0.0.0',  # すべてのインターフェースでリッスン
    'port': 8000,
    'buffer_size': 1024 * 1024,  # 1MB
    'timeout': 300,  # 5分
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'max_connections': 100,
    'enable_logging': True,
    'log_file': 'server.log',
    'log_level': 'INFO'
}

# セキュリティ設定
SECURITY_CONFIG = {
    'enable_cors': True,
    'allowed_origins': ['*'],
    'allowed_methods': ['GET', 'POST', 'OPTIONS', 'PUT', 'DELETE'],
    'allowed_headers': ['Content-Type', 'Content-Length', 'Range'],
    'max_upload_size': 50 * 1024 * 1024,  # 50MB
    'rate_limit': 1000,  # リクエスト/分
}

# ファイル転送設定
TRANSFER_CONFIG = {
    'chunk_size': 1024 * 1024,  # 1MBチャンク
    'enable_resume': True,
    'temp_dir': 'temp',
    'cleanup_interval': 3600,  # 1時間
}

# パフォーマンス設定
PERFORMANCE_CONFIG = {
    'enable_compression': True,
    'enable_caching': True,
    'cache_timeout': 3600,  # 1時間
    'enable_gzip': True,
    'gzip_level': 6,
} 