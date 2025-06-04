#!/bin/bash
# 确保生产环境使用正确的环境配置脚本
# 解决React环境变量优先级冲突问题

echo "🔧 确保生产环境使用正确的环境配置..."

# 检查是否在backend目录
if [ ! -d "../frontend" ]; then
    echo "❌ 错误: 请在backend目录下运行此脚本"
    exit 1
fi

cd ../frontend

echo "📋 当前环境文件状态:"
ls -la .env* 2>/dev/null || echo "   无环境文件"

echo ""
echo "🔍 检查环境变量冲突..."

# 检查各个文件中的REACT_APP_API_URL
conflict_found=false

if [ -f ".env" ]; then
    api_url=$(grep "REACT_APP_API_URL" ".env" 2>/dev/null | cut -d'=' -f2)
    if [ -n "$api_url" ]; then
        echo "   .env: $api_url"
        conflict_found=true
    fi
fi

if [ -f ".env.local" ]; then
    api_url=$(grep "REACT_APP_API_URL" ".env.local" 2>/dev/null | cut -d'=' -f2)
    if [ -n "$api_url" ]; then
        echo "   .env.local: $api_url"
        conflict_found=true
    fi
fi

if [ -f ".env.production" ]; then
    api_url=$(grep "REACT_APP_API_URL" ".env.production" 2>/dev/null | cut -d'=' -f2)
    if [ -n "$api_url" ]; then
        echo "   .env.production: $api_url"
    fi
fi

if [ -f ".env.production.local" ]; then
    api_url=$(grep "REACT_APP_API_URL" ".env.production.local" 2>/dev/null | cut -d'=' -f2)
    if [ -n "$api_url" ]; then
        echo "   .env.production.local: $api_url"
        conflict_found=true
    fi
fi

echo ""
if [ "$conflict_found" = true ]; then
    echo "⚠️  发现环境文件冲突，这些文件会覆盖.env.production的配置"
    echo ""
    echo "🎯 解决方案选择:"
    echo "1. 重命名冲突文件（推荐）"
    echo "2. 删除冲突文件"
    echo "3. 仅显示当前状态"
    
    read -p "请选择 (1/2/3): " choice
    
    case $choice in
        1)
            echo "📦 重命名冲突的环境文件..."
            
            # 备份并重命名.env.local（优先级高于.env.production）
            if [ -f ".env.local" ]; then
                backup_name=".env.local.disabled.$(date +%Y%m%d_%H%M%S)"
                mv ".env.local" "$backup_name"
                echo "✅ .env.local 已重命名为: $backup_name"
            fi
            
            # 备份并重命名.env（可能影响生产环境）
            if [ -f ".env" ]; then
                backup_name=".env.disabled.$(date +%Y%m%d_%H%M%S)"
                mv ".env" "$backup_name"
                echo "✅ .env 已重命名为: $backup_name"
            fi
            
            # 备份并重命名.env.production.local（最高优先级）
            if [ -f ".env.production.local" ]; then
                backup_name=".env.production.local.disabled.$(date +%Y%m%d_%H%M%S)"
                mv ".env.production.local" "$backup_name"
                echo "✅ .env.production.local 已重命名为: $backup_name"
            fi
            
            echo "🎉 冲突文件已处理完成"
            ;;
        2)
            echo "🗑️  删除冲突的环境文件..."
            
            if [ -f ".env.local" ]; then
                rm ".env.local"
                echo "✅ .env.local 已删除"
            fi
            
            if [ -f ".env" ]; then
                rm ".env"
                echo "✅ .env 已删除"
            fi
            
            if [ -f ".env.production.local" ]; then
                rm ".env.production.local"
                echo "✅ .env.production.local 已删除"
            fi
            
            echo "🎉 冲突文件已删除完成"
            ;;
        3)
            echo "📊 仅显示当前状态，不做修改"
            ;;
        *)
            echo "❌ 无效选择，退出"
            exit 1
            ;;
    esac
else
    echo "✅ 无环境文件冲突，.env.production将正确使用"
fi

echo ""
echo "📋 处理后的环境文件状态:"
ls -la .env* 2>/dev/null || echo "   无环境文件"

echo ""
echo "🔍 验证.env.production配置:"
if [ -f ".env.production" ]; then
    echo "✅ .env.production 存在"
    api_url=$(grep "REACT_APP_API_URL" .env.production | cut -d'=' -f2)
    echo "   API URL: $api_url"
    
    if [ "$api_url" = "http://9.135.87.101:7860/api" ]; then
        echo "✅ API URL 配置正确"
    else
        echo "❌ API URL 配置错误，应该是: http://9.135.87.101:7860/api"
    fi
else
    echo "❌ .env.production 不存在"
fi

echo ""
echo "💡 建议："
echo "1. 现在只保留 .env.production 文件"
echo "2. 生产环境构建时会正确使用 .env.production"
echo "3. 如需恢复其他环境文件，可以重命名备份文件"
echo ""
echo "🚀 现在可以安全地运行生产环境构建："
echo "   npm run build"
echo ""
echo "🔧 或者使用强制指定方式（更安全）："
echo "   REACT_APP_API_URL=http://9.135.87.101:7860/api npm run build" 