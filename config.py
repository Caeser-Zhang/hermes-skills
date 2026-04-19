"""
Ruby到Python测试转换器配置
包含所有映射规则和配置项
"""

# 断言映射表: RSpec expect -> pytest assert
ASSERTION_MAPPINGS = {
    # 基本断言
    'eq': lambda actual, expected: f'assert {actual} == {expected}',
    'be_truthy': lambda actual, _: f'assert {actual}',
    'be_falsy': lambda actual, _: f'assert not {actual}',
    'be_falsey': lambda actual, _: f'assert not {actual}',
    'be_nil': lambda actual, _: f'assert {actual} is None',
    'be': lambda actual, expected: f'assert {actual} is {expected}',
    
    # 比较断言
    'be >': lambda actual, expected: f'assert {actual} > {expected}',
    'be <': lambda actual, expected: f'assert {actual} < {expected}',
    'be >=': lambda actual, expected: f'assert {actual} >= {expected}',
    'be <=': lambda actual, expected: f'assert {actual} <= {expected}',
    
    # 集合断言
    'include': lambda actual, expected: f'assert {expected} in {actual}',
    'contain_exactly': lambda actual, expected: f'assert set({actual}) == set({expected})',
    
    # 类型断言
    'be_instance_of': lambda actual, expected: f'assert isinstance({actual}, {expected})',
    'be_kind_of': lambda actual, expected: f'assert isinstance({actual}, {expected})',
    
    # 字符串断言
    'start_with': lambda actual, expected: f'assert {actual}.startswith({expected})',
    'end_with': lambda actual, expected: f'assert {actual}.endswith({expected})',
    'match': lambda actual, expected: f'assert re.match({expected}, {actual})',
    
    # 异常断言
    'raise_error': lambda actual, expected: f'pytest.raises({expected})',
}

# Matcher映射表
MATCHER_MAPPINGS = {
    'to': 'positive',      # expect(x).to
    'not_to': 'negative',  # expect(x).not_to
    'to_not': 'negative',  # expect(x).to_not
}

# Mock方法映射
MOCK_MAPPINGS = {
    'double': 'Mock',
    'instance_double': 'Mock',
    'class_double': 'Mock',
    'spy': 'Mock',
    'instance_spy': 'Mock',
    'allow': 'patch.object',
    'receive': 'return_value',
    'receive_messages': 'side_effect',
}

# RSpec到pytest钩子映射
HOOK_MAPPINGS = {
    'before(:each)': 'def setup_method',
    'before(:all)': 'def setup_class',
    'before(:suite)': 'def pytest_configure',
    'after(:each)': 'def teardown_method',
    'after(:all)': 'def teardown_class',
    'after(:suite)': 'def pytest_unconfigure',
}

# 文件命名规则
FILE_NAMING = {
    'spec_pattern': '_spec.rb',
    'test_pattern': 'test_{}.py',
    'spec_dir': 'spec',
    'test_dir': 'tests',
    'helper_file': {
        'spec': 'spec_helper.rb',
        'test': 'conftest.py',
    },
}

# 目录映射
DIRECTORY_MAPPINGS = {
    'spec': 'tests',
    'lib': 'src',
    'app': 'app',
    'fixtures': 'fixtures',
}

# 需要安装的Python包
REQUIREMENTS = [
    'pytest>=7.0.0',
    'pytest-cov>=4.0.0',
    'pytest-mock>=3.10.0',
    'pytest-asyncio>=0.21.0',
    'factory-boy>=3.2.0',
]
