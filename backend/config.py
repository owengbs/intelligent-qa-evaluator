#!/usr/bin/env python3
"""
环境配置文件
支持本地开发环境和线上生产环境的配置
"""

import os
from dataclasses import dataclass

@dataclass
class Config:
    """基础配置类"""
    # 数据库配置
    DATABASE_PATH = 'database/qa_evaluation.db'
    
    def __post_init__(self):
        """数据类初始化后设置数据库URI"""
        # 使用绝对路径确保数据库文件可以正确创建和访问
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 创建数据库目录（如果不存在）
        db_dir = os.path.join(base_dir, 'database')
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"📁 创建数据库目录: {db_dir}")
        
        # 构建数据库文件完整路径
        db_path = os.path.join(base_dir, self.DATABASE_PATH)
        
        # 生产环境额外路径检查和权限验证
        if hasattr(self, 'ENVIRONMENT') and self.ENVIRONMENT == 'production':
            # 检查目录写入权限
            if not os.access(db_dir, os.W_OK):
                print(f"⚠️  警告: 数据库目录无写入权限: {db_dir}")
                # 尝试使用临时目录作为备选
                import tempfile
                temp_db_dir = os.path.join(tempfile.gettempdir(), 'qa_evaluator_db')
                os.makedirs(temp_db_dir, exist_ok=True)
                db_path = os.path.join(temp_db_dir, 'qa_evaluation.db')
                print(f"🔄 使用临时数据库路径: {db_path}")
        
        self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # 调试信息
        print(f"💾 数据库配置:")
        print(f"   - 基础目录: {base_dir}")
        print(f"   - 数据库路径: {db_path}")
        print(f"   - 数据库URI: {self.SQLALCHEMY_DATABASE_URI}")
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    
    def setup_logging(self):
        """配置日志目录"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            print(f"📁 创建日志目录: {log_dir}")
    
    # LLM配置
    LLM_MODEL = 'deepseek-v3-local-II'
    LLM_TIMEOUT = 120
    
    # 安全配置
    SECRET_KEY = 'your-secret-key-here'
    
    # CORS配置
    CORS_ORIGINS = ["*"]

@dataclass
class LocalConfig(Config):
    """本地开发环境配置"""
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5001
    DEBUG = True
    
    # API URL
    API_BASE_URL = 'http://localhost:5001/api'
    
    # 前端配置
    FRONTEND_HOST = 'localhost'
    FRONTEND_PORT = 3000
    
    # 环境标识
    ENVIRONMENT = 'local'

@dataclass
class ProductionConfig(Config):
    """线上生产环境配置"""
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 7860
    DEBUG = False
    
    # API URL
    API_BASE_URL = 'http://9.135.87.101:7860/api'
    
    # 前端配置
    FRONTEND_HOST = '9.135.87.101'
    FRONTEND_PORT = 8701
    
    # 环境标识
    ENVIRONMENT = 'production'
    
    # 生产环境特定配置
    LOG_LEVEL = 'WARNING'
    
    def __post_init__(self):
        """生产环境初始化"""
        super().__post_init__()
        # 设置日志
        self.setup_logging()
        print(f"🌐 生产环境配置完成")

def get_config():
    """根据环境变量获取配置"""
    env = os.getenv('APP_ENV', 'local').lower()
    
    if env == 'production':
        return ProductionConfig()
    else:
        return LocalConfig()

# 全局配置实例
config = get_config()

def print_config_info():
    """打印当前配置信息"""
    print(f"🌍 运行环境: {config.ENVIRONMENT}")
    print(f"🏠 服务器地址: {config.HOST}:{config.PORT}")
    print(f"🌐 API地址: {config.API_BASE_URL}")
    print(f"🖥️  前端地址: {config.FRONTEND_HOST}:{config.FRONTEND_PORT}")
    print(f"🔧 调试模式: {config.DEBUG}")
    
if __name__ == '__main__':
    print_config_info() 