#!/bin/bash

echo "🚀 启动视频生成工具Web服务..."
echo "=================================="

# 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p uploads
mkdir -p output/{t2i,i2v_flash,t2v_plus}
mkdir -p assets/{images,videos}
mkdir -p downloads

# 检查requirements.txt是否存在
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 未找到requirements.txt文件"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖包..."
pip3 install -r requirements.txt

# 检查必要的文件
required_files=(
    "app.py"
    "qwen_t2i_flash.py"
    "qwen_i2v_flash.py"
    "qwen_t2v_plus.py"
    "templates/index.html"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 错误: 未找到必要文件 $file"
        exit 1
    fi
done

echo "✅ 环境检查完成"
echo ""
echo "🌟 服务配置:"
echo "   - 端口: 5000"
echo "   - 访问地址: http://localhost:5000"
echo "   - 上传目录: ./uploads"
echo "   - 输出目录: ./output"
echo "   - 素材目录: ./assets"
echo ""
echo "📋 已启用的功能模块:"
echo "   🎨 文生图 (通义万相2.2-文生图-Flash)"
echo "   🎬 图生视频 (通义万相2.2-图生视频-Flash)"
echo "   🎥 文生视频 (通义万相2.2-文生视频-Plus)"
echo ""
echo "💡 使用提示:"
echo "   1. 将测试图片放入 assets/images/ 目录"
echo "   2. 在浏览器中打开 http://localhost:5000"
echo "   3. 选择对应的功能标签页进行测试"
echo "   4. 生成的结果会自动保存到 assets/ 目录"
echo ""
echo "🔑 注意: 请确保在各个API文件中配置了正确的API密钥"
echo ""

# 启动Flask应用
echo "🚀 启动Web服务..."
python3 app.py