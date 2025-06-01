"""
日志工具模块
提供统一的日志记录功能，支持不同级别的日志输出
"""
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

class Logger:
    """日志记录器类"""
    
    def __init__(self, name=None, log_level=logging.INFO):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            log_level: 日志级别
        """
        self.name = name or __name__
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(log_level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器 - 所有日志
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 错误日志文件处理器
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'error.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message, *args, **kwargs):
        """调试级别日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """信息级别日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """警告级别日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def warn(self, message, *args, **kwargs):
        """警告级别日志（别名）"""
        self.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """错误级别日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """严重错误级别日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message, *args, **kwargs):
        """异常日志（包含堆栈跟踪）"""
        self.logger.exception(message, *args, **kwargs)

# 全局日志记录器实例
_loggers = {}

def get_logger(name=None):
    """
    获取日志记录器实例
    
    Args:
        name: 日志记录器名称，通常使用 __name__
        
    Returns:
        Logger: 日志记录器实例
    """
    if name is None:
        name = 'app'
    
    if name not in _loggers:
        _loggers[name] = Logger(name)
    
    return _loggers[name]

# 便捷函数
def debug(message, *args, **kwargs):
    """调试日志"""
    get_logger().debug(message, *args, **kwargs)

def info(message, *args, **kwargs):
    """信息日志"""
    get_logger().info(message, *args, **kwargs)

def warning(message, *args, **kwargs):
    """警告日志"""
    get_logger().warning(message, *args, **kwargs)

def warn(message, *args, **kwargs):
    """警告日志（别名）"""
    warning(message, *args, **kwargs)

def error(message, *args, **kwargs):
    """错误日志"""
    get_logger().error(message, *args, **kwargs)

def critical(message, *args, **kwargs):
    """严重错误日志"""
    get_logger().critical(message, *args, **kwargs)

def exception(message, *args, **kwargs):
    """异常日志"""
    get_logger().exception(message, *args, **kwargs) 