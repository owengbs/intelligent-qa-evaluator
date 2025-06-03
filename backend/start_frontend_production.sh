#!/bin/bash
"""
生产环境前端启动脚本
"""

echo "🖥️  启动生产环境前端服务..."

# 检查是否在正确的目录
if [ ! -d "../frontend" ]; then
    echo "❌ 错误: 未找到前端目录，请确保在backend目录下运行此脚本"
    exit 1
fi

# 切换到前端目录
cd ../frontend

# 复制生产环境配置
echo "🔧 配置生产环境..."
cp ../backend/env_production.txt .env.production

# 显示配置信息
echo "🌍 环境: 生产环境"
echo "🏠 前端地址: http://9.135.87.101:8701"
echo "🌐 API地址: http://9.135.87.101:7860/api"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 检查并安装serve包
echo "🔍 检查serve包..."
if ! npx serve --version &> /dev/null; then
    echo "📦 安装serve包..."
    npm install -g serve || {
        echo "⚠️  全局安装失败，尝试本地安装..."
        npm install serve --save-dev
    }
fi

# 生产环境构建
echo "🔨 构建生产版本..."
npm run build

# 检查构建是否成功
if [ ! -d "build" ]; then
    echo "❌ 错误: 构建失败，未找到build目录"
    exit 1
fi

# 启动前端服务（生产模式）
echo "🚀 启动前端服务 (端口: 8701)..."

# 方法1: 尝试使用全局npx serve
if npx serve --version &> /dev/null 2>&1; then
    echo "✅ 使用 npx serve 启动服务..."
    npx serve -s build -l 8701 --cors
# 方法2: 尝试使用本地serve
elif [ -f "node_modules/.bin/serve" ]; then
    echo "✅ 使用本地serve启动服务..."
    ./node_modules/.bin/serve -s build -l 8701 --cors
# 方法3: 使用Python HTTP服务器 + CORS支持
elif command -v python3 &> /dev/null; then
    echo "⚠️  serve不可用，使用Python3 HTTP服务器..."
    cd build
    python3 -c "
import http.server
import socketserver
from http.server import SimpleHTTPRequestHandler
import sys

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

PORT = 8701
Handler = CORSRequestHandler

try:
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f'✅ 服务器运行在端口 {PORT}')
        print(f'🌐 访问地址: http://9.135.87.101:{PORT}')
        httpd.serve_forever()
except KeyboardInterrupt:
    print('\n🛑 服务器已停止')
    sys.exit(0)
except Exception as e:
    print(f'❌ 启动失败: {e}')
    sys.exit(1)
"
# 方法4: 使用Node.js内置服务器
elif command -v node &> /dev/null; then
    echo "⚠️  使用Node.js内置服务器..."
    cd build
    node -e "
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8701;
const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.wav': 'audio/wav',
    '.mp4': 'video/mp4',
    '.woff': 'application/font-woff',
    '.ttf': 'application/font-ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.otf': 'application/font-otf',
    '.wasm': 'application/wasm'
};

const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
    
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(__dirname, 'index.html');
    }
    
    const extname = String(path.extname(filePath)).toLowerCase();
    const contentType = mimeTypes[extname] || 'application/octet-stream';
    
    fs.readFile(filePath, (error, content) => {
        if (error) {
            res.writeHead(500);
            res.end('服务器错误: ' + error.code);
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, () => {
    console.log('✅ Node.js服务器运行在端口', PORT);
    console.log('🌐 访问地址: http://9.135.87.101:' + PORT);
});
"
else
    echo "❌ 错误: 无法找到合适的HTTP服务器"
    echo "💡 建议安装Node.js和npm，然后运行: npm install -g serve"
    echo "🔧 手动启动: serve -s build -l 8701"
    exit 1
fi 