#!/bin/bash
# Ruby到Python测试转换验证脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
TEST_REPOS="$SKILL_DIR/test_repos"
CONVERTER="$SKILL_DIR/convert.py"

echo "========================================"
echo "Ruby到Python测试转换验证"
echo "========================================"
echo ""

# 检查Python依赖
echo "检查Python依赖..."
pip install -q pytest pytest-mock 2>/dev/null || true
echo "✓ 依赖检查完成"
echo ""

# 测试1: 简单RSpec项目
echo "测试1: 简单RSpec项目转换"
echo "----------------------------------------"
OUTPUT_DIR="/tmp/python_tests_simple"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

python "$CONVERTER" "$TEST_REPOS/simple/spec" -o "$OUTPUT_DIR" -v

if [ -f "$OUTPUT_DIR/test_calculator.py" ]; then
    echo "✓ calculator_spec.rb 转换成功"
else
    echo "✗ calculator_spec.rb 转换失败"
fi

if [ -f "$OUTPUT_DIR/test_user.py" ]; then
    echo "✓ user_spec.rb 转换成功"
else
    echo "✗ user_spec.rb 转换失败"
fi

echo ""
echo "生成的文件:"
ls -la "$OUTPUT_DIR"/*.py 2>/dev/null || echo "没有生成Python文件"

if [ -f "$OUTPUT_DIR/test_calculator.py" ]; then
    echo ""
    echo "test_calculator.py 内容预览:"
    head -30 "$OUTPUT_DIR/test_calculator.py"
fi

echo ""
echo ""

# 测试2: 中等复杂度RSpec项目
echo "测试2: 中等复杂度RSpec项目转换"
echo "----------------------------------------"
OUTPUT_DIR="/tmp/python_tests_medium"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

python "$CONVERTER" "$TEST_REPOS/medium/spec" -o "$OUTPUT_DIR" -v

if [ -f "$OUTPUT_DIR/test_post.py" ]; then
    echo "✓ post_spec.rb 转换成功"
else
    echo "✗ post_spec.rb 转换失败"
fi

if [ -f "$OUTPUT_DIR/test_email_service.py" ]; then
    echo "✓ email_service_spec.rb 转换成功"
else
    echo "✗ email_service_spec.rb 转换失败"
fi

echo ""
echo ""

# 测试3: Minitest项目
echo "测试3: Minitest项目转换"
echo "----------------------------------------"
OUTPUT_DIR="/tmp/python_tests_minitest"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

python "$CONVERTER" "$TEST_REPOS/minitest/spec" -o "$OUTPUT_DIR" --framework minitest -v

if [ -f "$OUTPUT_DIR/test_calculator.py" ]; then
    echo "✓ calculator_test.rb 转换成功"
else
    echo "✗ calculator_test.rb 转换失败"
fi

if [ -f "$OUTPUT_DIR/test_user_service.py" ]; then
    echo "✓ user_service_test.rb 转换成功"
else
    echo "✗ user_service_test.rb 转换失败"
fi

echo ""
echo ""

# 验证Python测试可执行性
echo "验证Python测试可执行性"
echo "========================================"
echo ""

cd "/tmp/python_tests_simple"
echo "运行简单项目测试..."
python -m pytest -v --tb=short 2>&1 | head -50 || echo "测试执行有问题"

echo ""
echo "========================================"
echo "验证完成!"
echo "========================================"
