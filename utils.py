"""
工具函数模块
包含命名转换、文件操作等辅助功能
"""
import os
import re
from pathlib import Path
from typing import List, Optional


def ruby_to_python_class_name(name: str) -> str:
    """
    Ruby类名转Python类名
    User::Admin -> UserAdmin
    """
    return name.replace('::', '')


def ruby_to_python_method_name(name: str) -> str:
    """
    Ruby方法名转Python方法名
    user_name -> user_name (相同)
    is_admin? -> is_admin
    calculate_total! -> calculate_total
    """
    name = name.rstrip('?!')
    return name.replace('?', '').replace('!', '')


def spec_to_test_filename(filename: str) -> str:
    """
    Ruby spec文件名转Python测试文件名
    user_spec.rb -> test_user.py
    users_controller_spec.rb -> test_users_controller.py
    """
    # 移除_spec.rb后缀
    name = filename.replace('_spec.rb', '').replace('.rb', '')
    # 转换为test_开头
    return f'test_{name}.py'


def ruby_require_to_python_import(require_line: str) -> str:
    """
    Ruby require转Python import
    require 'spec_helper' -> import pytest
    require_relative '../models/user' -> from ..models import User
    """
    # 提取require的模块名
    match = re.search(r'require(?:_relative)?\s+["\'](.+?)["\']', require_line)
    if not match:
        return ''
    
    module = match.group(1)
    
    # 特殊处理
    if module == 'spec_helper':
        return 'import pytest'
    elif module == 'rails_helper':
        return 'import pytest\nimport django'
    else:
        # 转换为Python import
        parts = module.split('/')
        class_name = ''.join(p.capitalize() for p in parts[-1].split('_'))
        module_path = '.'.join(parts)
        return f'from {module_path} import {class_name}'


def snake_to_camel(name: str) -> str:
    """snake_case转CamelCase"""
    return ''.join(word.capitalize() for word in name.split('_'))


def camel_to_snake(name: str) -> str:
    """CamelCase转snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def create_directory_structure(base_path: str, directories: List[str]) -> None:
    """创建目录结构"""
    for directory in directories:
        path = Path(base_path) / directory
        path.mkdir(parents=True, exist_ok=True)


def read_file_content(file_path: str) -> str:
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file_content(file_path: str, content: str) -> None:
    """写入文件内容"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def find_ruby_files(directory: str, pattern: str = '*_spec.rb') -> List[str]:
    """查找Ruby测试文件"""
    ruby_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('_spec.rb') or file.endswith('_test.rb'):
                ruby_files.append(os.path.join(root, file))
    return ruby_files


def parse_method_args(args_string: str) -> dict:
    """
    解析Ruby方法参数
    do_something(arg1, arg2: value) -> {'args': ['arg1'], 'kwargs': {'arg2': 'value'}}
    """
    # 简化实现，实际需要更复杂的解析
    return {'args': [], 'kwargs': {}}


def extract_string_literal(code: str) -> str:
    """
    提取字符串字面量
    "hello" -> hello
    'world' -> world
    """
    match = re.match(r'["\'](.+?)["\']', code.strip())
    if match:
        return match.group(1)
    return code


def is_test_method(method_name: str) -> bool:
    """判断是否是测试方法"""
    return method_name.startswith('it ') or method_name.startswith('test_')
