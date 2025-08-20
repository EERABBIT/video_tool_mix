#!/bin/bash

# 通义千问视频生成工具启动脚本

echo "🚀 启动通义千问视频生成工具..."
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"

# 检查并安装依赖
echo ""
echo "📦 检查依赖包..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "📥 安装依赖包..."
    pip3 install -r requirements.txt
else
    echo "✅ 依赖包已安装"
fi

# 设置API密钥（如果未设置）
if [ -z "$DASHSCOPE_API_KEY" ]; then
    export DASHSCOPE_API_KEY="sk-c4af8d8ed01d43a587eda9b8c3b32058"
    echo "🔑 使用默认API密钥"
else
    echo "🔑 使用环境变量中的API密钥"
fi

# 创建必要的目录
echo ""
echo "📁 创建目录结构..."
mkdir -p assets/images assets/videos 
mkdir -p output/keyframe_plus output/t2i output/i2v_flash output/t2v_plus output/image_edit
mkdir -p uploads test_output downloads
echo "✅ 目录创建完成"

# 检查必要的文件
echo ""
echo "📋 检查核心文件..."
required_files=(
    "app.py"
    "qwen_t2i_flash.py"
    "qwen_i2v_flash.py"
    "qwen_t2v_plus.py"
    "qwen_keyframe_plus.py"
    "qwen_image_edit.py"
    "templates/index.html"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (缺失)"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo ""
    echo "⚠️ 警告: 部分文件缺失，某些功能可能无法使用"
    echo ""
fi

# 显示功能模块
echo ""
echo "🎯 已启用的功能模块:"
echo "   🎨 文生图 (wanx-v1)"
echo "   🎬 图生视频 (wanx-i2v-flash)"
echo "   🎥 文生视频 (wanx2.0-t2v-plus)"
echo "   🎞️ 首尾帧视频 (wanx2.1-kf2v-plus)"
echo "   🖼️ 图片编辑 (qwen-image-edit) ⭐新功能"

# 启动服务
echo ""
echo "🌐 启动Web服务..."
echo "================================"
echo "📍 访问地址: http://localhost:30001"
echo "📍 端口: 30001"
echo "📁 素材目录: ./assets/"
echo "📁 输出目录: ./output/"
echo "================================"
echo ""
echo "💡 使用提示:"
echo "  1. 打开浏览器访问 http://localhost:30001"
echo "  2. 选择对应功能进行测试"
echo "  3. 生成结果自动保存到output目录"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动Flask应用
python3 app.py