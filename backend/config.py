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
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    
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