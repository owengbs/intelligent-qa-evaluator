#!/bin/bash
"""
前端配置验证脚本
验证生产环境前端配置是否正确
"""

echo "🔍 前端配置验证工具"
echo "="*50

# 检查是否在backend目录
if [ ! -d "../frontend" ]; then
    echo "❌ 错误: 请在backend目录下运行此脚本"
    exit 1
fi

cd ../frontend

echo "📋 1. 检查环境配置文件..."

# 检查.env.production文件
if [ -f ".env.production" ]; then
    echo "✅ .env.production 文件存在"
    echo "📄 内容:"
    cat .env.production
    echo ""
    
    # 验证API URL配置
    API_URL=$(grep "REACT_APP_API_URL" .env.production | cut -d'=' -f2)
    if [ "$API_URL" = "http://9.135.87.101:7860/api" ]; then
        echo "✅ API URL配置正确: $API_URL"
    else
        echo "❌ API URL配置错误: $API_URL"
        echo "🔧 应该是: http://9.135.87.101:7860/api"
    fi
else
    echo "❌ .env.production 文件不存在"
    echo "💡 请运行 start_frontend_production.sh 创建配置"
fi

echo ""
echo "📋 1.1 检查环境文件冲突..."

# 检查会影响.env.production的其他环境文件
conflict_found=false

if [ -f ".env.local" ]; then
    echo "⚠️  发现 .env.local 文件（优先级高于.env.production）"
    LOCAL_API_URL=$(grep "REACT_APP_API_URL" .env.local 2>/dev/null | cut -d'=' -f2)
    if [ -n "$LOCAL_API_URL" ]; then
        echo "   API URL: $LOCAL_API_URL"
        echo "💡 建议: 运行 ./ensure_production_env.sh 处理冲突"
        conflict_found=true
    fi
fi

if [ -f ".env" ]; then
    if grep -q "REACT_APP_API_URL" .env 2>/dev/null; then
        echo "⚠️  发现 .env 文件包含 REACT_APP_API_URL"
        ENV_API_URL=$(grep "REACT_APP_API_URL" .env | cut -d'=' -f2)
        echo "   API URL: $ENV_API_URL"
        echo "💡 建议: 运行 ./ensure_production_env.sh 处理冲突"
        conflict_found=true
    fi
fi

if [ -f ".env.production.local" ]; then
    echo "⚠️  发现 .env.production.local 文件（最高优先级）"
    LOCAL_PROD_API_URL=$(grep "REACT_APP_API_URL" .env.production.local 2>/dev/null | cut -d'=' -f2)
    if [ -n "$LOCAL_PROD_API_URL" ]; then
        echo "   API URL: $LOCAL_PROD_API_URL"
        conflict_found=true
    fi
fi

if [ "$conflict_found" = false ]; then
    echo "✅ 无环境文件冲突"
fi

echo ""
echo "📋 2. 检查package.json配置..."

# 检查proxy配置
if grep -q '"proxy"' package.json; then
    PROXY_VALUE=$(grep '"proxy"' package.json | cut -d'"' -f4)
    echo "⚠️  发现proxy配置: $PROXY_VALUE"
    echo "💡 生产环境建议移除proxy配置"
else
    echo "✅ 无proxy配置（适合生产环境）"
fi

echo ""
echo "📋 3. 检查构建结果..."

if [ -d "build" ]; then
    echo "✅ build目录存在"
    
    # 检查主要的JS文件
    MAIN_JS_FILE=$(find build/static/js -name "main.*.js" 2>/dev/null | head -1)
    if [ -n "$MAIN_JS_FILE" ]; then
        echo "✅ 找到主JS文件: $(basename $MAIN_JS_FILE)"
        
        # 检查API配置是否正确编译进去
        if grep -q "9.135.87.101:7860" "$MAIN_JS_FILE"; then
            echo "✅ 构建文件包含正确的API地址"
        else
            echo "⚠️  构建文件中未找到预期的API地址"
            echo "🔍 当前构建中的API配置:"
            grep -o "http://[^\"]*api" "$MAIN_JS_FILE" | head -3 || echo "   未找到API配置"
        fi
    else
        echo "❌ 未找到主JS文件"
    fi
    
    # 检查index.html
    if [ -f "build/index.html" ]; then
        echo "✅ index.html存在"
    else
        echo "❌ index.html不存在"
    fi
else
    echo "❌ build目录不存在"
    echo "💡 请先运行构建: npm run build"
fi

echo ""
echo "📋 4. 检查后端配置源文件..."

if [ -f "../backend/env_production.txt" ]; then
    echo "✅ 后端生产环境配置存在"
    echo "📄 内容:"
    cat ../backend/env_production.txt
else
    echo "❌ 后端生产环境配置不存在"
fi

echo ""
echo "📋 5. 网络连通性测试..."

# 测试后端API是否可达
echo "🌐 测试后端API连通性..."
if command -v curl &> /dev/null; then
    if curl -s --connect-timeout 5 "http://9.135.87.101:7860/api/health" > /dev/null; then
        echo "✅ 后端API可达"
    else
        echo "⚠️  后端API不可达或未启动"
        echo "💡 请确保后端服务已启动: python app.py"
    fi
else
    echo "⚠️  curl命令不可用，跳过连通性测试"
fi

echo ""
echo "="*50
echo "🎯 配置验证完成"

# 总结建议
echo ""
echo "💡 配置建议:"
echo "1. 确保.env.production中API URL为: http://9.135.87.101:7860/api"
echo "2. 生产环境移除package.json中的proxy配置"
echo "3. 重新构建前端以确保配置生效: npm run build"
echo "4. 启动前端服务: serve -s build -l 8701"
echo "5. 访问地址: http://9.135.87.101:8701" 