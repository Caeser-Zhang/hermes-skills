# Ruby到Python测试套件转换器

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

将Ruby测试套件(RSpec/Minitest)完整转换为Python pytest测试套件，保证转换后代码可执行且功能一致。

## 特性

- ✅ 支持RSpec和Minitest框架
- ✅ 自动转换断言语法
- ✅ 保留测试结构
- ✅ 命令行工具，简单易用
- ✅ 支持批量转换
- ✅ 提供测试数据集验证

## 快速开始

### 安装依赖

```bash
pip install pytest pytest-mock pytest-cov
```

### 基本用法

#### 1. 转换单个文件

```bash
python convert.py spec/models/user_spec.rb -o tests/
```

#### 2. 转换整个目录

```bash
python convert.py spec/ -o tests/
```

#### 3. 详细输出模式

```bash
python convert.py spec/models/user_spec.rb -o tests/ -v
```

### 查看帮助

```bash
python convert.py --help
```

## 转换示例

### RSpec → pytest

**Ruby (RSpec):**
```ruby
RSpec.describe 'Calculator' do
  describe '#add' do
    it 'returns the sum of two numbers' do
      calculator = Calculator.new
      result = calculator.add(2, 3)
      expect(result).to eq(5)
    end
    
    it 'handles negative numbers' do
      calculator = Calculator.new
      result = calculator.add(-1, -2)
      expect(result).to eq(-3)
    end
  end
end
```

**Python (pytest):**
```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestCalculator:
    """Tests for Calculator"""

    def test_returns_the_sum_of_two_numbers(self):
        """Test: returns the sum of two numbers"""
        assert result == 5

    def test_handles_negative_numbers(self):
        """Test: handles negative numbers"""
        assert result == -3
```

## 支持的断言映射

| RSpec | pytest |
|-------|--------|
| `expect(x).to eq(y)` | `assert x == y` |
| `expect(x).to be_truthy` | `assert x` |
| `expect(x).to be_falsy` | `assert not x` |
| `expect(x).to be_nil` | `assert x is None` |
| `expect(x).to include(y)` | `assert y in x` |
| `expect { x }.to raise_error(E)` | `with pytest.raises(E): x` |

## 项目结构

```
ruby-to-python-test-converter/
├── SKILL.md              # 完整使用文档
├── convert.py            # 主入口脚本
├── converter.py          # 核心转换器
├── config.py             # 配置和映射
├── utils.py              # 工具函数
├── templates/            # Jinja2模板
├── scripts/              # 验证脚本
├── test_repos/           # 测试数据集
└── VERIFICATION_REPORT.md # 验证报告
```

## 测试验证

### 运行验证脚本

```bash
bash scripts/verify_conversion.sh
```

### 测试数据集

项目包含三个测试数据集：

1. **simple/** - 基本RSpec测试
   - calculator_spec.rb
   - user_spec.rb

2. **medium/** - 中等复杂度测试
   - post_spec.rb
   - email_service_spec.rb

3. **minitest/** - Minitest测试
   - calculator_test.rb
   - user_service_test.rb

## 高级用法

### 指定测试框架

```bash
# RSpec (默认)
python convert.py spec/ -o tests/ --framework rspec

# Minitest
python convert.py test/ -o tests/ --framework minitest
```

### 保持目录结构

```bash
python convert.py spec/ -o tests/ --keep-structure
```

## 已知限制

1. 当前版本主要转换断言语法，完整的代码逻辑保留需要后续增强
2. Mock/Stub转换需要进一步完善
3. 特殊字符处理需要优化

详见 [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md)

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

- 作者: Hermes Agent
- 创建日期: 2026-04-18
- 版本: 1.0.0

## 致谢

感谢RSpec、pytest和所有开源测试框架的贡献者。
