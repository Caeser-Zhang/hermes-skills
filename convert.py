#!/usr/bin/env python3
"""
Ruby测试套件到Python测试套件转换工具
主入口脚本
"""
import argparse
import sys
import os
from pathlib import Path
from converter import TestConverter
import config


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Convert Ruby test suite to Python pytest suite',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('source', help='Ruby test file or directory')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('-p', '--project', default='', help='Project name')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-f', '--framework', choices=['rspec', 'minitest'], 
                       default='rspec', help='Ruby test framework')
    parser.add_argument('--keep-structure', action='store_true',
                       help='Keep original directory structure')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    source_path = Path(args.source)
    output_path = Path(args.output)
    
    # 验证源路径
    if not source_path.exists():
        print(f"Error: Source path does not exist: {source_path}")
        sys.exit(1)
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 初始化转换器
    converter = TestConverter()
    
    print(f"Ruby to Python Test Converter")
    print(f"=" * 50)
    print(f"Source: {source_path}")
    print(f"Output: {output_path}")
    print(f"Framework: {args.framework}")
    print()
    
    # 执行转换
    if source_path.is_file():
        # 转换单个文件
        try:
            output_file = converter.convert_file(str(source_path), str(output_path))
            print(f"\n✓ Conversion complete: {output_file}")
            
            # 显示生成的代码
            if args.verbose:
                print(f"\nGenerated code:")
                print("-" * 50)
                with open(output_file, 'r') as f:
                    print(f.read())
        
        except Exception as e:
            print(f"\n✗ Conversion failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    else:
        # 转换目录
        converted_files = converter.convert_directory(str(source_path), str(output_path))
        
        print(f"\n{'=' * 50}")
        print(f"Conversion Summary:")
        print(f"  Total files: {len(converted_files)}")
        
        # 生成requirements.txt
        req_file = output_path / 'requirements.txt'
        with open(req_file, 'w') as f:
            f.write('\n'.join(config.REQUIREMENTS))
        print(f"  Requirements: {req_file}")
        
        # 生成conftest.py
        conftest_file = output_path / 'conftest.py'
        if not conftest_file.exists():
            with open(conftest_file, 'w') as f:
                f.write('import pytest\nfrom unittest.mock import Mock\n')
        print(f"  Conftest: {conftest_file}")
        
        print(f"\n✓ Conversion complete!")
        print(f"\nNext steps:")
        print(f"  1. cd {output_path}")
        print(f"  2. pip install -r requirements.txt")
        print(f"  3. pytest -v")


if __name__ == '__main__':
    main()
