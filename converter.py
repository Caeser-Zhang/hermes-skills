"""
Ruby测试代码转换器
支持RSpec和Minitest到pytest的转换
"""
import re
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import config
import utils


@dataclass
class TestCase:
    """测试用例数据结构"""
    name: str
    description: str
    assertions: List[str] = field(default_factory=list)
    setup_code: List[str] = field(default_factory=list)
    teardown_code: List[str] = field(default_factory=list)
    let_vars: Dict[str, str] = field(default_factory=dict)
    mocks: List[str] = field(default_factory=list)
    body: str = ''


@dataclass
class TestClass:
    """测试类数据结构"""
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup_methods: Dict[str, str] = field(default_factory=dict)
    shared_contexts: List[str] = field(default_factory=list)
    parent_class: str = ''
    imports: List[str] = field(default_factory=list)


class RubyParser:
    """Ruby代码解析器"""
    
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split('\n')
        self.pos = 0
    
    def parse_rspec_describe(self, code: str) -> List[TestClass]:
        """解析RSpec describe块"""
        test_classes = []
        
        # 匹配 describe 块
        describe_pattern = r'describe\s+["\'](.+?)["\']\s+do'
        matches = list(re.finditer(describe_pattern, code, re.MULTILINE))
        
        for match in matches:
            test_class = TestClass(
                name=utils.snake_to_camel(match.group(1).replace(' ', '_')),
                description=match.group(1)
            )
            
            # 提取describe块内容
            start = match.end()
            block_content = self._extract_block(code, start)
            
            # 解析块内容
            self._parse_describe_content(block_content, test_class)
            test_classes.append(test_class)
        
        return test_classes
    
    def _extract_block(self, code: str, start: int) -> str:
        """提取do...end块内容"""
        depth = 1
        pos = start
        block_start = start
        
        while pos < len(code) and depth > 0:
            if code[pos:pos+2] == 'do':
                depth += 1
                pos += 2
            elif code[pos:pos+3] == 'end':
                depth -= 1
                pos += 3
            else:
                pos += 1
        
        return code[block_start:pos-3].strip()
    
    def _parse_describe_content(self, content: str, test_class: TestClass):
        """解析describe块内容"""
        # 解析 let 变量
        self._parse_let_vars(content, test_class)
        
        # 解析 before/after 钩子
        self._parse_hooks(content, test_class)
        
        # 解析 it 块（测试用例）
        self._parse_it_blocks(content, test_class)
        
        # 解析 context 块
        self._parse_context_blocks(content, test_class)
    
    def _parse_let_vars(self, content: str, test_class: TestClass):
        """解析let变量定义"""
        let_pattern = r'let!?(?:\s*\(([^)]+)\))?\s+:(\w+)\s+\{([^}]+)\}'
        
        for match in re.finditer(let_pattern, content):
            var_name = match.group(2)
            var_value = match.group(3).strip()
            test_class.test_cases.append(TestCase(
                name=f'let_{var_name}',
                description=f'let variable {var_name}',
                body=f'{var_name} = {var_value}'
            ))
    
    def _parse_hooks(self, content: str, test_class: TestClass):
        """解析before/after钩子"""
        # before(:each)
        before_each_pattern = r'before\(:each\)\s+do\s*([^}]+)\s*end'
        for match in re.finditer(before_each_pattern, content):
            test_class.setup_methods['setup_method'] = match.group(1).strip()
        
        # before(:all)
        before_all_pattern = r'before\(:all\)\s+do\s*([^}]+)\s*end'
        for match in re.finditer(before_all_pattern, content):
            test_class.setup_methods['setup_class'] = match.group(1).strip()
    
    def _parse_it_blocks(self, content: str, test_class: TestClass):
        """解析it块（测试用例）"""
        it_pattern = r'it\s+["\'](.+?)["\']\s+do\s*([\s\S]*?)\s*end'
        
        for match in re.finditer(it_pattern, content):
            test_desc = match.group(1)
            test_body = match.group(2).strip()
            
            test_case = TestCase(
                name=f'test_{utils.camel_to_snake(test_desc.replace(" ", "_"))}',
                description=test_desc,
                body=test_body
            )
            
            # 转换断言
            test_case.assertions = self._convert_assertions(test_case.body)
            test_class.test_cases.append(test_case)
    
    def _parse_context_blocks(self, content: str, test_class: TestClass):
        """解析context块"""
        context_pattern = r'context\s+["\'](.+?)["\']\s+do\s*([\s\S]*?)\s*end'
        
        for match in re.finditer(context_pattern, content):
            context_content = match.group(2)
            
            # Context作为嵌套describe处理
            # 这里简化处理，直接解析其中的it块
            self._parse_it_blocks(context_content, test_class)
    
    def _convert_assertions(self, code: str) -> List[str]:
        """转换RSpec断言到pytest断言"""
        assertions = []
        
        # expect(x).to eq(y)
        eq_pattern = r'expect\(([^)]+)\)\.to\s+eq\(([^)]+)\)'
        for match in re.finditer(eq_pattern, code):
            actual = match.group(1)
            expected = match.group(2)
            assertions.append(f'assert {actual} == {expected}')
        
        # expect(x).to be_truthy
        truthy_pattern = r'expect\(([^)]+)\)\.to\s+be_truthy'
        for match in re.finditer(truthy_pattern, code):
            actual = match.group(1)
            assertions.append(f'assert {actual}')
        
        # expect(x).to be_falsy
        falsy_pattern = r'expect\(([^)]+)\)\.to\s+be_fals(?:y|ey)'
        for match in re.finditer(falsy_pattern, code):
            actual = match.group(1)
            assertions.append(f'assert not {actual}')
        
        # expect(x).to be_nil
        nil_pattern = r'expect\(([^)]+)\)\.to\s+be_nil'
        for match in re.finditer(nil_pattern, code):
            actual = match.group(1)
            assertions.append(f'assert {actual} is None')
        
        # expect(x).to include(y)
        include_pattern = r'expect\(([^)]+)\)\.to\s+include\(([^)]+)\)'
        for match in re.finditer(include_pattern, code):
            actual = match.group(1)
            expected = match.group(2)
            assertions.append(f'assert {expected} in {actual}')
        
        # expect { }.to raise_error(ErrorClass)
        raise_pattern = r'expect\s*\{([^}]+)\}\s*\.to\s+raise_error\(([^)]+)\)'
        for match in re.finditer(raise_pattern, code):
            block_code = match.group(1)
            error_class = match.group(2)
            assertions.append(f'with pytest.raises({error_class}):\n    {block_code}')
        
        return assertions


class PytestGenerator:
    """pytest代码生成器"""
    
    def generate_test_file(self, test_class: TestClass) -> str:
        """生成pytest测试文件"""
        lines = []
        
        # 导入
        lines.append('import pytest')
        lines.append('from unittest.mock import Mock, patch, MagicMock')
        if test_class.imports:
            lines.extend(test_class.imports)
        lines.append('')
        lines.append('')
        
        # 测试类
        lines.append(f'class Test{test_class.name}:')
        lines.append(f'    """Tests for {test_class.description}"""')
        lines.append('')
        
        # Setup方法
        if 'setup_method' in test_class.setup_methods:
            lines.append('    def setup_method(self):')
            for line in test_class.setup_methods['setup_method'].split('\n'):
                lines.append(f'        {line}')
            lines.append('')
        
        if 'setup_class' in test_class.setup_methods:
            lines.append('    @classmethod')
            lines.append('    def setup_class(cls):')
            for line in test_class.setup_methods['setup_class'].split('\n'):
                lines.append(f'        {line}')
            lines.append('')
        
        # 测试方法
        for test_case in test_class.test_cases:
            if test_case.name.startswith('let_'):
                continue  # let变量跳过
            
            lines.append(f'    def {test_case.name}(self):')
            lines.append(f'        """Test: {test_case.description}"""')
            
            # 添加断言
            if test_case.assertions:
                for assertion in test_case.assertions:
                    lines.append(f'        {assertion}')
            else:
                lines.append('        # TODO: Add assertions')
            
            lines.append('')
            lines.append('')
        
        return '\n'.join(lines)
    
    def generate_conftest(self, fixtures: Dict[str, Any]) -> str:
        """生成conftest.py"""
        lines = ['import pytest', 'from unittest.mock import Mock', '', '']
        
        for fixture_name, fixture_code in fixtures.items():
            lines.append('@pytest.fixture')
            lines.append(f'def {fixture_name}():')
            for line in fixture_code.split('\n'):
                lines.append(f'    {line}')
            lines.append('')
            lines.append('')
        
        return '\n'.join(lines)


class TestConverter:
    """测试转换器主类"""
    
    def __init__(self):
        self.parser = RubyParser('')
        self.generator = PytestGenerator()
    
    def convert_file(self, ruby_file_path: str, output_dir: str) -> str:
        """转换单个Ruby测试文件"""
        # 读取Ruby代码
        with open(ruby_file_path, 'r', encoding='utf-8') as f:
            ruby_code = f.read()
        
        # 解析
        self.parser.content = ruby_code
        test_classes = self.parser.parse_rspec_describe(ruby_code)
        
        # 生成Python代码
        python_code_lines = []
        for test_class in test_classes:
            python_code = self.generator.generate_test_file(test_class)
            python_code_lines.append(python_code)
        
        # 写入文件
        output_filename = utils.spec_to_test_filename(os.path.basename(ruby_file_path))
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(python_code_lines))
        
        return output_path
    
    def convert_directory(self, ruby_dir: str, output_dir: str) -> List[str]:
        """转换整个目录"""
        converted_files = []
        
        # 查找所有Ruby测试文件
        ruby_files = utils.find_ruby_files(ruby_dir)
        
        for ruby_file in ruby_files:
            try:
                output_path = self.convert_file(ruby_file, output_dir)
                converted_files.append(output_path)
                print(f"✓ Converted: {ruby_file} -> {output_path}")
            except Exception as e:
                print(f"✗ Failed to convert {ruby_file}: {e}")
        
        return converted_files
