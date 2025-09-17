#!/bin/bash
# 自动点击器启动脚本

echo "🚀 正在启动自动点击器..."
echo "📍 当前目录: $(pwd)"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查依赖是否安装
echo "📦 检查依赖包..."
pip list | grep -q pyautogui
if [ $? -ne 0 ]; then
    echo "📥 安装依赖包..."
    pip install -r requirements.txt
fi

echo "✅ 所有依赖已就绪"
echo "🖱️ 启动自动点击器..."
echo ""
echo "⚠️  重要提醒："
echo "   - 首次运行需要在系统偏好设置中授权辅助功能权限"
echo "   - 路径：系统偏好设置 > 安全性与隐私 > 辅助功能"
echo "   - 需要为终端或Python授权"
echo ""

# 运行程序
python auto_clicker.py

