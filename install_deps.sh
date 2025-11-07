#!/bin/bash

# 安装req.txt中的依赖
# 使用方法: bash install_deps.sh 或 ./install_deps.sh

echo "开始安装Python依赖..."

# 检查req.txt文件是否存在
if [ ! -f "req.txt" ]; then
    echo "错误: req.txt文件不存在!"
    exit 1
fi

# 统计总行数
total_lines=$(wc -l < req.txt)
echo "总共需要安装 $total_lines 个包"

# 计数器
installed=0
failed=0

# 逐行读取并安装
while IFS= read -r line; do
    # 跳过空行和注释行
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi

    # 提取包名（去掉版本号）
    package_name=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)

    echo "正在安装: $line ($((installed + failed + 1))/$total_lines)"

    # 尝试安装
    if pip install "$line" > /dev/null 2>&1; then
        echo "✅ 安装成功: $line"
        ((installed++))
    else
        echo "❌ 安装失败: $line"
        ((failed++))
    fi

done < req.txt

echo ""
echo "安装完成!"
echo "成功: $installed 个包"
echo "失败: $failed 个包"

if [ $failed -gt 0 ]; then
    echo "有 $failed 个包安装失败，请检查错误信息"
    exit 1
else
    echo "所有包安装成功!"
fi
