#!/bin/bash

echo "🔧 修复serve包冲突问题..."

# 显示当前serve的状态
echo "📊 当前serve状态检查:"
echo "全局serve命令: $(which serve 2>/dev/null || echo '未找到')"
echo "npx serve版本: $(npx serve --version 2>/dev/null || echo '不可用')"

# 方法1: 清理冲突的serve文件
echo "🧹 清理冲突的serve文件..."
if [ -f "/usr/local/bin/serve" ]; then
    echo "发现冲突文件: /usr/local/bin/serve"
    sudo rm -f /usr/local/bin/serve 2>/dev/null && echo "✅ 已删除冲突文件" || echo "❌ 删除失败，可能需要权限"
fi

# 方法2: 卸载并重新安装serve
echo "🔄 重新安装serve..."
npm uninstall -g serve 2>/dev/null || true
npm install -g serve --force

# 方法3: 如果全局安装失败，尝试本地安装
if ! npx serve --version &> /dev/null; then
    echo "⚠️  全局安装失败，尝试本地安装..."
    cd ../frontend
    npm install serve --save-dev --force
    cd ../backend
fi

# 验证修复结果
echo "✅ 修复完成，验证结果:"
if npx serve --version &> /dev/null; then
    echo "✅ serve 现在可以正常使用"
    npx serve --version
else
    echo "❌ serve 仍然不可用"
    echo "💡 建议手动执行："
    echo "   sudo rm -f /usr/local/bin/serve"
    echo "   npm install -g serve --force"
fi

echo "🎉 修复脚本执行完成" 