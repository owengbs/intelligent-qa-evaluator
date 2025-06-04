#!/bin/bash
"""
生产环境前端启动脚本
修复IP和端口配置问题
"""

echo "🖥️  启动生产环境前端服务..."

# 检查是否在正确的目录
if [ ! -d "../frontend" ]; then
    echo "❌ 错误: 未找到前端目录，请确保在backend目录下运行此脚本"
    exit 1
fi

# 切换到前端目录
cd ../frontend

# 备份现有环境配置（如果存在）
if [ -f ".env.production" ]; then
    echo "💾 备份现有生产环境配置..."
    cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)
fi

# 复制生产环境配置
echo "🔧 配置生产环境..."
cp ../backend/env_production.txt .env.production

# 验证配置是否正确复制
echo "🔍 验证环境配置..."
if [ -f ".env.production" ]; then
    echo "✅ 环境配置文件已创建"
    echo "📋 当前配置内容:"
    cat .env.production
    echo ""
else
    echo "❌ 环境配置文件复制失败"
    exit 1
fi

# 检查并修复package.json中的proxy配置（生产环境不需要）
echo "🔧 检查package.json proxy配置..."
if grep -q '"proxy"' package.json; then
    echo "⚠️  发现proxy配置，备份并移除..."
    # 备份package.json
    cp package.json package.json.backup.$(date +%Y%m%d_%H%M%S)
    
    # 移除proxy配置（生产环境不需要）
    if command -v jq &> /dev/null; then
        # 使用jq移除proxy
        jq 'del(.proxy)' package.json > package.json.tmp && mv package.json.tmp package.json
        echo "✅ 使用jq移除proxy配置"
    else
        # 使用sed移除proxy行
        sed -i.bak '/\"proxy\":/d' package.json
        echo "✅ 使用sed移除proxy配置"
    fi
else
    echo "✅ 未发现proxy配置"
fi

# 🔧 新增：处理环境文件冲突，确保使用.env.production
echo "🔧 处理环境文件冲突，确保使用.env.production..."

# 检查是否存在会覆盖.env.production的文件
conflict_found=false

if [ -f ".env.local" ]; then
    echo "⚠️  发现.env.local文件，会覆盖.env.production配置"
    backup_name=".env.local.disabled.$(date +%Y%m%d_%H%M%S)"
    mv ".env.local" "$backup_name"
    echo "✅ .env.local 已重命名为: $backup_name"
    conflict_found=true
fi

if [ -f ".env" ]; then
    # 检查.env是否包含冲突的API URL
    if grep -q "REACT_APP_API_URL" .env; then
        echo "⚠️  发现.env文件包含API URL配置，可能影响生产环境"
        backup_name=".env.disabled.$(date +%Y%m%d_%H%M%S)"
        mv ".env" "$backup_name"
        echo "✅ .env 已重命名为: $backup_name"
        conflict_found=true
    fi
fi

if [ "$conflict_found" = true ]; then
    echo "🎉 环境文件冲突已解决"
else
    echo "✅ 无环境文件冲突"
fi

# 显示最终配置信息
echo "🌍 环境: 生产环境"
echo "🏠 前端地址: http://9.135.87.101:8701"
echo "🌐 API地址: http://9.135.87.101:7860/api"
echo "📡 实际API配置: $(grep REACT_APP_API_URL .env.production || echo '未找到')"

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

# 清理之前的构建
if [ -d "build" ]; then
    echo "🧹 清理旧的构建文件..."
    rm -rf build
fi

# 生产环境构建
echo "🔨 构建生产版本..."
REACT_APP_API_URL=http://9.135.87.101:7860/api npm run build

# 检查构建是否成功
if [ ! -d "build" ]; then
    echo "❌ 错误: 构建失败，未找到build目录"
    exit 1
fi

echo "✅ 构建成功，build目录已生成"

# 验证构建结果中的配置
echo "🔍 验证构建结果..."
if [ -f "build/static/js/main.*.js" ]; then
    MAIN_JS_FILE=$(find build/static/js -name "main.*.js" | head -1)
    if grep -q "9.135.87.101:7860" "$MAIN_JS_FILE"; then
        echo "✅ 构建文件中包含正确的API地址"
    else
        echo "⚠️  构建文件中可能未包含正确的API地址"
        echo "🔍 检查构建中的API配置..."
        grep -o "http://[^\"]*api" "$MAIN_JS_FILE" | head -3 || echo "未找到API配置"
    fi
fi

# 启动前端服务（生产模式）
echo "🚀 启动前端服务 (端口: 8701)..."

# 方法1: 尝试使用全局npx serve
if npx serve --version &> /dev/null 2>&1; then
    echo "✅ 使用 npx serve 启动服务..."
    echo "🌐 访问地址: http://9.135.87.101:8701"
    npx serve -s build -l 8701 --cors
# 方法2: 尝试使用本地serve
elif [ -f "node_modules/.bin/serve" ]; then
    echo "✅ 使用本地serve启动服务..."
    echo "🌐 访问地址: http://9.135.87.101:8701"
    ./node_modules/.bin/serve -s build -l 8701 --cors
# 方法3: 使用Python HTTP服务器 + CORS支持
elif command -v python3 &> /dev/null; then
    echo "⚠️  serve不可用，使用Python3 HTTP服务器..."
    cd build
    echo "🌐 访问地址: http://9.135.87.101:8701"
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
    with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
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
    echo "🌐 访问地址: http://9.135.87.101:8701"
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

server.listen(PORT, '0.0.0.0', () => {
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