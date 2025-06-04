#!/bin/bash
# 项目整体状态检查脚本

echo "🚀 智能化问答评估系统 - 项目状态检查"
echo "="*60

# 检查项目版本
echo "📦 项目版本信息:"
if [ -f "app.py" ]; then
    version=$(grep "VERSION.*=" app.py | head -1 | cut -d'"' -f2)
    echo "   当前版本: $version"
else
    echo "   ❌ 无法获取版本信息"
fi

# 1. 后端状态检查
echo ""
echo "🖥️  后端服务状态:"

# 检查SQLAlchemy兼容性
if python3 -c "
try:
    import sqlalchemy
    print('✅ SQLAlchemy版本:', sqlalchemy.__version__)
    
    # 检查Engine.execute兼容性
    if hasattr(sqlalchemy.engine.Engine, 'execute'):
        print('✅ 向后兼容性: Engine.execute可用')
    else:
        print('⚠️  新版本: 仅支持connection.execute')
except Exception as e:
    print('❌ SQLAlchemy检查失败:', e)
" 2>/dev/null; then
    echo "   数据库适配: 正常"
else
    echo "   ❌ 数据库适配: 失败"
fi

# 检查数据库连接
if python3 test_db_connection.py 2>/dev/null | grep -q "✅"; then
    echo "   ✅ 数据库连接: 正常"
else
    echo "   ⚠️  数据库连接: 需要检查"
fi

# 检查API服务
if curl -s --connect-timeout 3 "http://9.135.87.101:7860/api/health" > /dev/null 2>&1; then
    echo "   ✅ API服务: 运行中"
else
    echo "   ⚠️  API服务: 未运行或不可达"
fi

# 2. 前端状态检查
echo ""
echo "🌐 前端服务状态:"

cd ../frontend 2>/dev/null || {
    echo "   ❌ 前端目录不存在"
    exit 1
}

# 检查环境配置
env_status="✅ 正常"
if [ -f ".env.local" ] || [ -f ".env" ] && grep -q "REACT_APP_API_URL" .env 2>/dev/null; then
    env_status="⚠️  存在冲突文件"
fi

echo "   环境配置: $env_status"

if [ -f ".env.production" ]; then
    api_url=$(grep "REACT_APP_API_URL" .env.production | cut -d'=' -f2)
    if [ "$api_url" = "http://9.135.87.101:7860/api" ]; then
        echo "   ✅ API配置: $api_url"
    else
        echo "   ❌ API配置错误: $api_url"
    fi
else
    echo "   ❌ 缺少生产环境配置"
fi

# 检查构建状态
if [ -d "build" ]; then
    main_js=$(find build/static/js -name "main.*.js" 2>/dev/null | head -1)
    if [ -n "$main_js" ] && grep -q "9.135.87.101:7860" "$main_js"; then
        echo "   ✅ 构建状态: 包含正确API地址"
    else
        echo "   ⚠️  构建状态: 需要重新构建"
    fi
else
    echo "   ❌ 构建状态: 未构建"
fi

# 检查前端服务
if curl -s --connect-timeout 3 "http://9.135.87.101:8701" > /dev/null 2>&1; then
    echo "   ✅ 前端服务: 运行中"
else
    echo "   ⚠️  前端服务: 未运行"
fi

cd ../backend

# 3. 功能模块状态
echo ""
echo "🧩 功能模块状态:"

# 检查分类服务
if python3 -c "
try:
    from services.classification_service_sqlite import ClassificationService_sqlite
    print('✅ 分类服务: 可用')
except Exception as e:
    print('❌ 分类服务: 异常 -', str(e))
" 2>/dev/null; then
    echo "   分类服务: 正常"
else
    echo "   ❌ 分类服务: 异常"
fi

# 检查知识库
if [ -f "knowledge_base.db" ]; then
    echo "   ✅ 知识库: 存在"
else
    echo "   ❌ 知识库: 不存在"
fi

# 4. 脚本工具状态
echo ""
echo "🛠️  工具脚本状态:"

scripts=(
    "verify_frontend_config.sh:前端配置验证"
    "ensure_production_env.sh:环境冲突处理"
    "start_frontend_production.sh:生产启动脚本"
    "test_db_connection.py:数据库测试"
)

for script_info in "${scripts[@]}"; do
    script=$(echo "$script_info" | cut -d':' -f1)
    desc=$(echo "$script_info" | cut -d':' -f2)
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "   ✅ $desc ($script)"
    else
        echo "   ❌ $desc ($script): 不可用"
    fi
done

# 5. 文档状态
echo ""
echo "📚 文档状态:"

docs=(
    "PRODUCTION_FIX_SUMMARY.md:SQLAlchemy修复文档"
    "FRONTEND_CONFIG_FIX_SUMMARY.md:前端配置修复文档"
    "PRODUCTION_ENV_GUIDE.md:生产环境配置指南"
    "../README.md:项目说明文档"
)

for doc_info in "${docs[@]}"; do
    doc=$(echo "$doc_info" | cut -d':' -f1)
    desc=$(echo "$doc_info" | cut -d':' -f2)
    if [ -f "$doc" ]; then
        echo "   ✅ $desc"
    else
        echo "   ❌ $desc: 缺失"
    fi
done

# 6. Git状态
echo ""
echo "📝 Git状态:"
if git status --porcelain | grep -q .; then
    echo "   ⚠️  存在未提交的更改"
    git status --porcelain | head -5
else
    echo "   ✅ 工作目录干净"
fi

echo "   当前分支: $(git branch --show-current)"
echo "   最新提交: $(git log -1 --oneline)"

# 7. 总结建议
echo ""
echo "💡 操作建议:"

if [ "$env_status" != "✅ 正常" ]; then
    echo "   🔧 运行 ./ensure_production_env.sh 处理环境冲突"
fi

if ! curl -s --connect-timeout 3 "http://9.135.87.101:7860/api/health" > /dev/null 2>&1; then
    echo "   🚀 启动后端服务: python app.py"
fi

if ! curl -s --connect-timeout 3 "http://9.135.87.101:8701" > /dev/null 2>&1; then
    echo "   🌐 启动前端服务: ./start_frontend_production.sh"
fi

echo ""
echo "🎯 快速启动命令："
echo "   后端: python app.py"
echo "   前端: ./start_frontend_production.sh"
echo "   验证: ./verify_frontend_config.sh"
echo ""
echo "="*60 