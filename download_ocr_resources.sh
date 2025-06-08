#!/bin/bash

# OCR资源预下载脚本
# 解决首次使用时语言包下载缓慢的问题

echo "🚀 开始下载OCR语言包资源..."

# 创建存储目录
mkdir -p frontend/public/ocr-resources
cd frontend/public/ocr-resources

echo "📦 下载英文语言包..."
curl -L -o eng.traineddata.gz "https://tessdata.projectnaptha.com/4.0.0/eng.traineddata.gz"

echo "📦 下载中文简体语言包..."
curl -L -o chi_sim.traineddata.gz "https://tessdata.projectnaptha.com/4.0.0/chi_sim.traineddata.gz"

echo "📦 下载Tesseract核心文件..."
curl -L -o tesseract-core.wasm.js "https://unpkg.com/tesseract.js-core@4.0.4/tesseract-core.wasm.js"

echo "📦 下载Worker文件..."
curl -L -o worker.min.js "https://unpkg.com/tesseract.js@4.1.4/dist/worker.min.js"

# 检查下载结果
echo "🔍 检查下载结果..."

for file in eng.traineddata.gz chi_sim.traineddata.gz tesseract-core.wasm.js worker.min.js; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo "✅ $file ($size)"
    else
        echo "❌ $file 下载失败"
    fi
done

echo ""
echo "💡 使用说明："
echo "1. 将下载的文件部署到您的服务器"
echo "2. 修改OCR配置指向本地资源路径"
echo "3. 这样就不需要每次从海外CDN下载了"

echo ""
echo "🎉 OCR资源下载完成！" 