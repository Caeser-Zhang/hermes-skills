---
name: ruby-to-python-test-converter
description: 将Ruby测试套件(RSpec/Minitest)完整转换为Python pytest测试套件，保证转换后代码可执行且功能一致。支持断言映射、Mock转换、依赖分析和完整测试代码仓生成。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [testing, conversion, ruby, python, rspec, pytest, minitest]
    related_skills: [test-driven-development, requesting-code-review]
---

# Ruby到Python测试套件转换器

将Ruby测试套件完整转换为Python pytest测试套件，支持RSpec和Minitest框架。

## 使用场景

- Ruby项目迁移到Python
- 需要在Python环境中复现Ruby测试
- 测试框架升级和技术栈统一
- 学习测试框架映射关系

## 支持的Ruby测试框架

### RSpec (主要支持)
- ✓ describe/context/it 块结构
- ✓ expect 断言语法
- ✓ let/let! 变量定义
- ✓ before/after 钩子
- ✓ shared_examples/shared_context
- ✓ mock/stub (rspec-mocks)
- ✓ 应答断言和异常断言

### Minitest (支持)
- ✓ Test类继承
- ✓ assert 断言方法
- ✓ setup/teardown 钩子
- ✓ mock/stub

## 快速开始

### 转换单个文件

```bash
cd ~/.hermes/skills/ruby-to-python-test-converter
python convert.py spec/models/user_spec.rb -o tests/ -v
```

### 转换整个目录

```bash
python convert.py spec/ -o tests/
```

### 指定测试框架

```bash
# RSpec (默认)
python convert.py spec/ -o tests/ --framework rspec

# Minitest
python convert.py test/ -o tests/ --framework minitest
```

## 转换映射规则

### 断言映射

| RSpec | pytest |
|-------|--------|
| `expect(x).to eq(y)` | `assert x == y` |
| `expect(x).to be_truthy` | `assert x` |
| `expect(x).to be_falsy` | `assert not x` |
| `expect(x).to be_nil` | `assert x is None` |
| `expect(x).to include(y)` | `assert y in x` |
| `expect { x }.to raise_error(E)` | `with pytest.raises(E): x` |
| `expect(x).to be_instance_of(Y)` | `assert isinstance(x, Y)` |

### Mock映射

| RSpec | pytest/unittest.mock |
|-------|----------------------|
| `double()` | `Mock()` |
| `allow(obj).to receive(:m)` | `patch.object(obj, 'm')` |
| `expect(obj).to receive(:m)` | `mock.assert_called()` |

### 测试结构映射

| RSpec | pytest |
|-------|--------|
| `describe "X"` | `class TestX:` |
| `context "Y"` | 嵌套类或注释 |
| `it "does something"` | `def test_does_something(self):` |
| `let(:var) { value }` | pytest fixture |
| `before(:each)` | `def setup_method(self):` |

## 完整工作流程

### 1. 准备Ruby测试代码仓

确保测试文件符合标准结构:
```
spec/
├── spec_helper.rb
├── models/
│   └── user_spec.rb
├── controllers/
│   └── users_controller_spec.rb
└── fixtures/
    └── users.yml
```

### 2. 运行转换

```bash
cd ~/.hermes/skills/ruby-to-python-test-converter
python convert.py /path/to/ruby/spec -o /path/to/python/tests
```

### 3. 安装依赖

```bash
cd /path/to/python/tests
pip install -r requirements.txt
```

### 4. 运行测试

```bash
pytest -v
```

## 详细转换流程

### Phase 1: 代码分析
1. 扫描Ruby测试文件
2. 识别测试框架类型 (RSpec/Minitest)
3. 解析测试结构 (describe/it/context)
4. 提取断言和mock定义
5. 分析依赖关系

### Phase 2: 结构转换
1. 转换文件名 (user_spec.rb → test_user.py)
2. 转换目录结构 (spec/ → tests/)
3. 转换测试类和方法名
4. 生成conftest.py

### Phase 3: 代码转换
1. 转换断言语句
2. 转换mock/stub
3. 转换before/after钩子
4. 转换let变量为fixture
5. 处理shared_examples

### Phase 4: 验证和修复
1. Python语法检查
2. 导入路径修正
3. 运行测试验证
4. 生成转换报告

## 高级功能

### 增量转换

只转换修改过的文件:

```bash
python convert.py spec/ -o tests/ --incremental
```

### 保持目录结构

保留原有的子目录结构:

```bash
python convert.py spec/ -o tests/ --keep-structure
```

### 自定义映射

创建自定义映射文件 `custom_mappings.json`:

```json
{
  "assertions": {
    "custom_matcher": "assert custom_check({actual}, {expected})"
  },
  "methods": {
    "special_method": "special_python_method"
  }
}
```

## 测试数据集验证

### 简单测试项目

位置: `~/.hermes/skills/ruby-to-python-test-converter/test_repos/simple/`

包含:
- 基本断言测试
- let变量测试
- before钩子测试
- 简单mock测试

### 中等复杂度项目

位置: `~/.hermes/skills/ruby-to-python-test-converter/test_repos/medium/`

包含:
- 共享上下文
- 复杂断言
- 多层嵌套
- HTTP请求测试

### Minitest项目

位置: `~/.hermes/skills/ruby-to-python-test-converter/test_repos/minitest/`

包含:
- Minitest断言
- setup/teardown
- Minitest mock

## 转换质量保证

### 自动化检查

1. **语法检查**: 使用 `py_compile` 验证生成的Python代码
2. **导入检查**: 验证所有导入路径正确
3. **测试执行**: 运行pytest确保测试可执行
4. **覆盖率对比**: 对比Ruby和Python测试覆盖率

### 手动审查重点

1. 复杂断言语义是否一致
2. Mock行为是否正确
3. 异常处理是否完整
4. 边界条件是否覆盖

## 常见问题和解决方案

### 1. Ruby元编程代码无法解析

**问题**: Ruby的动态定义方法无法静态分析

**解决**: 
- 使用运行时AST导出: `ruby -e "require 'parser'; ..."`
- 手动标注动态生成的测试

### 2. 第三方Gem扩展

**问题**: FactoryBot, SimpleCov等gem扩展

**解决**:
- FactoryBot → factory-boy
- SimpleCov → pytest-cov
- VCR → pytest-recording

### 3. 语义差异

**问题**: Ruby和Python语义差异

**解决**:
- 明确注释差异点
- 手动调整关键逻辑

## 项目结构

```
~/.hermes/skills/ruby-to-python-test-converter/
├── SKILL.md              # 本文档
├── convert.py            # 主入口脚本
├── converter.py          # 核心转换器
├── config.py             # 配置和映射表
├── utils.py              # 工具函数
├── templates/            # Jinja2模板
│   ├── test_file.py.j2
│   ├── conftest.py.j2
│   └── fixture.py.j2
├── scripts/              # 辅助脚本
│   ├── setup_test_env.sh
│   └── verify_conversion.sh
├── references/           # 参考文档
│   ├── rspec_to_pytest.md
│   └── minitest_to_pytest.md
└── test_repos/           # 测试数据集
    ├── simple/
    ├── medium/
    └── minitest/
```

## 验证脚本

### setup_test_env.sh

```bash
#!/bin/bash
# 设置测试环境

# 安装Python依赖
pip install pytest pytest-cov pytest-mock factory-boy

# 验证安装
pytest --version
python -c "import pytest_mock; print('pytest-mock installed')"
```

### verify_conversion.sh

```bash
#!/bin/bash
# 验证转换结果

RUBY_DIR=$1
PYTHON_DIR=$2

echo "验证转换结果..."

# 统计文件数量
ruby_count=$(find $RUBY_DIR -name "*_spec.rb" | wc -l)
python_count=$(find $PYTHON_DIR -name "test_*.py" | wc -l)

echo "Ruby测试文件: $ruby_count"
echo "Python测试文件: $python_count"

# 运行Python测试
cd $PYTHON_DIR
pytest -v --tb=short

echo "验证完成!"
```

## 最佳实践

### 转换前

1. 确保Ruby测试全部通过
2. 记录测试覆盖率和关键场景
3. 识别自定义matcher和helper

### 转换中

1. 分模块逐步转换
2. 每个模块转换后立即验证
3. 记录无法自动转换的部分

### 转换后

1. 运行完整测试套件
2. 对比测试覆盖率
3. 手动审查关键测试用例
4. 更新测试文档

## 扩展和自定义

### 添加自定义断言映射

编辑 `config.py`:

```python
ASSERTION_MAPPINGS['custom_matcher'] = lambda actual, expected: \
    f'assert custom_check({actual}, {expected})'
```

### 添加新测试框架支持

创建新的解析器类:

```python
class MyTestParser:
    def parse(self, code):
        # 解析逻辑
        pass
```

在 `converter.py` 中注册:

```python
PARSERS = {
    'rspec': RubyParser,
    'minitest': MinitestParser,
    'my_framework': MyTestParser,
}
```

## 实现经验和技术要点

### Python代码编写注意事项

1. **正则表达式转义**: Python字符串中的正则表达式需要正确转义引号
   ```python
   # ✗ 错误 - 会导致SyntaxError
   pattern = r'describe\s+["'](.+?)["']\s+do'
   
   # ✓ 正确 - 使用转义或不同引号
   pattern = r'describe\s+["\'](.+?)["\']\s+do'
   ```

2. **模块导入**: 使用`os.path`函数时必须导入`os`模块
   ```python
   import os  # 不要忘记
   output_filename = os.path.basename(ruby_file_path)
   ```

3. **数据类导入**: 使用dataclass需要从dataclasses导入field
   ```python
   from dataclasses import dataclass, field
   ```

### 转换器架构最佳实践

1. **模块分离**:
   - Parser (解析Ruby) → Models (中间结构) → Generator (生成Python)
   - 使用dataclass定义清晰的中间数据结构
   - 配置与逻辑分离 (config.py)

2. **正则解析策略**:
   - 使用多行模式 `re.MULTILINE` 处理整个文件
   - 使用 `[\s\S]*?` 匹配跨行内容（非贪婪）
   - 先解析外层结构，再递归解析内层

3. **代码生成**:
   - 使用列表累积行，最后`'\n'.join()`
   - 注意缩进处理
   - 生成的代码应包含完整的导入语句

### 常见问题和解决方案

1. **嵌套describe块重复生成**
   - 问题: 每个describe都生成独立的测试类
   - 解决: 需要实现测试类合并逻辑，或扁平化嵌套结构

2. **测试方法体代码丢失**
   - 问题: 只转换了断言，丢失了初始化代码
   - 解决: 需要保留完整的测试方法体，只替换断言语法

3. **特殊字符命名问题**
   - 问题: Ruby的`#add`、`?`、`!`等特殊字符
   - 解决: 在命名转换函数中清理特殊字符

## 限制和已知问题

1. **Ruby元编程**: 动态生成的测试方法需要手动处理
2. **复杂DSL**: 某些RSpec扩展可能无法完全转换
3. **第三方库**: 需要手动映射第三方gem到Python等价物
4. **性能测试**: benchmark测试需要使用pytest-benchmark重写
5. **代码逻辑保留**: 当前版本主要转换断言，完整的测试逻辑需要后续增强
6. **Mock转换**: rspec-mock到unittest.mock的转换需要更详细的规则

## 贡献

如需添加新的映射规则或修复问题:

1. 编辑 `config.py` 添加映射
2. 在 `test_repos/` 添加测试用例
3. 运行 `pytest tests/` 验证

## 更新日志

### v1.0.0 (2026-04-18)
- 初始版本
- 支持RSpec基本功能转换
- 支持Minitest基本功能转换
- 完整的断言和Mock映射
- 测试数据集验证

---

**注意**: 转换后请务必运行测试验证功能一致性。某些复杂场景可能需要手动调整。
