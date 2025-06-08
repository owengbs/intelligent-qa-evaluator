#!/bin/bash

echo "🖥️  简化版生产环境前端启动..."

# 检查是否在正确的目录
if [ ! -d "../frontend" ]; then
    echo "❌ 错误: 未找到前端目录，请确保在backend目录下运行此脚本"
    exit 1
fi

# 切换到前端目录
cd ../frontend

# 设置生产环境变量
export REACT_APP_API_URL=http://9.135.87.101:7860/api

echo "🔧 配置生产环境..."
echo "🌍 环境: 生产环境"
echo "🏠 前端地址: http://9.135.87.101:8701"
echo "🌐 API地址: $REACT_APP_API_URL"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 清理之前的构建
if [ -d "build" ]; then
    echo "🧹 清理旧的构建文件..."
    rm -rf build
fi

# 构建项目
echo "🔨 构建生产版本..."
npm run build

# 检查构建是否成功
if [ ! -d "build" ]; then
    echo "❌ 错误: 构建失败，未找到build目录"
    exit 1
fi

echo "✅ 构建成功"

# 启动服务的多种方式
echo "🚀 启动前端服务..."

# 方式1: 检查serve是否可用（不强制安装）
if command -v serve &> /dev/null; then
    echo "✅ 使用已安装的serve启动..."
    echo "🌐 访问地址: http://9.135.87.101:8701"
    serve -s build -l 8701 --cors

# 方式2: 使用npx serve（如果可用）
elif npx serve --version &> /dev/null 2>&1; then
    echo "✅ 使用npx serve启动..."
    echo "🌐 访问地址: http://9.135.87.101:8701"
    npx serve -s build -l 8701 --cors

# 方式3: 使用Python3
elif command -v python3 &> /dev/null; then
    echo "✅ 使用Python3 HTTP服务器..."
    cd build
    echo "🌐 访问地址: http://9.135.87.101:8701"
    python3 -m http.server 8701 --bind 0.0.0.0

# 方式4: 使用Node.js
elif command -v node &> /dev/null; then
    echo "✅ 使用Node.js HTTP服务器..."
    cd build
    echo "🌐 访问地址: http://9.135.87.101:8701"
    node -e "
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8701;

const server = http.createServer((req, res) => {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
    
    // SPA fallback
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(__dirname, 'index.html');
    }
    
    fs.readFile(filePath, (error, content) => {
        if (error) {
            res.writeHead(500);
            res.end('Error: ' + error.code);
        } else {
            const ext = path.extname(filePath);
            let contentType = 'text/html';
            
            switch(ext) {
                case '.js': contentType = 'text/javascript'; break;
                case '.css': contentType = 'text/css'; break;
                case '.json': contentType = 'application/json'; break;
                case '.png': contentType = 'image/png'; break;
                case '.jpg': contentType = 'image/jpg'; break;
                case '.gif': contentType = 'image/gif'; break;
                case '.svg': contentType = 'image/svg+xml'; break;
            }
            
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log('✅ 服务器运行在端口', PORT);
});
"

else
    echo "❌ 错误: 无法找到合适的HTTP服务器"
    echo "💡 请安装以下任一工具："
    echo "   - Node.js + serve: npm install -g serve"
    echo "   - Python3: apt-get install python3"
    echo "🔧 或者手动启动: cd build && python3 -m http.server 8701"
    exit 1
fi 