import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from twinself.core.config import config


class DataValidator:
    """Validates TwinSelf data files."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_json_file(self, filepath: Path) -> bool:
        """Validate JSON file structure."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it's a list
            if not isinstance(data, list):
                self.errors.append(f"{filepath}: Must be a JSON array")
                return False
            
            # Validate episodic data structure
            if 'episodic_data' in str(filepath):
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        self.errors.append(f"{filepath}[{i}]: Must be an object")
                        continue
                    
                    if 'user_query' not in item:
                        self.errors.append(f"{filepath}[{i}]: Missing 'user_query'")
                    if 'your_response' not in item:
                        self.errors.append(f"{filepath}[{i}]: Missing 'your_response'")
                    
                    # Check for empty values
                    if not item.get('user_query', '').strip():
                        self.warnings.append(f"{filepath}[{i}]: Empty 'user_query'")
                    if not item.get('your_response', '').strip():
                        self.warnings.append(f"{filepath}[{i}]: Empty 'your_response'")
            
            # Validate procedural data structure
            elif 'procedural_data' in str(filepath):
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        self.errors.append(f"{filepath}[{i}]: Must be an object")
                        continue
                    
                    if 'rule_name' not in item:
                        self.errors.append(f"{filepath}[{i}]: Missing 'rule_name'")
                    if 'rule_content' not in item:
                        self.errors.append(f"{filepath}[{i}]: Missing 'rule_content'")
            
            return True
            
        except json.JSONDecodeError as e:
            self.errors.append(f"{filepath}: Invalid JSON - {e}")
            return False
        except Exception as e:
            self.errors.append(f"{filepath}: Error - {e}")
            return False
    
    def validate_markdown_file(self, filepath: Path) -> bool:
        """Validate markdown file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                self.warnings.append(f"{filepath}: Empty file")
                return False
            
            # Check for minimum content length
            if len(content) < 50:
                self.warnings.append(f"{filepath}: Very short content ({len(content)} chars)")
            
            return True
            
        except Exception as e:
            self.errors.append(f"{filepath}: Error reading file - {e}")
            return False
    
    def check_data_quality(self) -> Tuple[int, int]:
        """Check overall data quality."""
        stats = {
            'semantic_files': 0,
            'episodic_files': 0,
            'procedural_files': 0,
            'episodic_examples': 0,
            'procedural_rules': 0
        }
        
        # Count semantic files
        semantic_dir = Path(config.semantic_data_dir)
        if semantic_dir.exists():
            stats['semantic_files'] = len(list(semantic_dir.glob('*.md'))) + len(list(semantic_dir.glob('*.txt')))
        
        # Count episodic examples
        episodic_dir = Path(config.episodic_data_dir)
        if episodic_dir.exists():
            for json_file in episodic_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            stats['episodic_files'] += 1
                            stats['episodic_examples'] += len(data)
                except Exception:
                    pass
        
        # Count procedural rules
        procedural_dir = Path(config.procedural_data_dir)
        if procedural_dir.exists():
            for json_file in procedural_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            stats['procedural_files'] += 1
                            stats['procedural_rules'] += len(data)
                except Exception:
                    pass
        
        # Quality checks
        if stats['semantic_files'] == 0:
            self.errors.append("No semantic data files found")
        elif stats['semantic_files'] < 3:
            self.warnings.append(f"Only {stats['semantic_files']} semantic files (recommend at least 3)")
        
        if stats['episodic_examples'] == 0:
            self.errors.append("No episodic examples found")
        elif stats['episodic_examples'] < 10:
            self.warnings.append(f"Only {stats['episodic_examples']} episodic examples (recommend at least 10)")
        
        if stats['procedural_rules'] == 0:
            self.warnings.append("No procedural rules found (will use defaults)")
        
        return stats


def main():
    parser = argparse.ArgumentParser(description="Validate TwinSelf data files")
    parser.add_argument('--check-json', action='store_true', help='Validate JSON files')
    parser.add_argument('--check-markdown', action='store_true', help='Validate Markdown files')
    parser.add_argument('--quality-check', action='store_true', help='Check data quality')
    
    args = parser.parse_args()
    
    validator = DataValidator()
    
    print("TwinSelf Data Validation")
    print("=" * 60)
    
    # Validate JSON files
    if args.check_json:
        print("\nValidating JSON files...")
        json_files = []
        json_files.extend(Path(config.episodic_data_dir).glob('*.json'))
        json_files.extend(Path(config.procedural_data_dir).glob('*.json'))
        
        for json_file in json_files:
            validator.validate_json_file(json_file)
        
        print(f"  Checked {len(json_files)} JSON files")
    
    # Validate Markdown files
    if args.check_markdown:
        print("\nValidating Markdown files...")
        md_files = list(Path(config.semantic_data_dir).glob('*.md'))
        md_files.extend(Path(config.semantic_data_dir).glob('*.txt'))
        
        for md_file in md_files:
            validator.validate_markdown_file(md_file)
        
        print(f"  Checked {len(md_files)} Markdown files")
    
    # Quality check
    if args.quality_check:
        print("\nData Quality Check...")
        stats = validator.check_data_quality()
        print(f"  Semantic files: {stats['semantic_files']}")
        print(f"  Episodic files: {stats['episodic_files']}")
        print(f"  Episodic examples: {stats['episodic_examples']}")
        print(f"  Procedural files: {stats['procedural_files']}")
        print(f"  Procedural rules: {stats['procedural_rules']}")
    
    # Print results
    print("\n" + "=" * 60)
    
    if validator.warnings:
        print(f"\n{len(validator.warnings)} Warnings:")
        for warning in validator.warnings:
            print(f"  - {warning}")
    
    if validator.errors:
        print(f"\n{len(validator.errors)} Errors:")
        for error in validator.errors:
            print(f"  - {error}")
        print("\nValidation FAILED")
        sys.exit(1)
    else:
        print("\nValidation PASSED")
        if validator.warnings:
            print("(with warnings)")
        sys.exit(0)


if __name__ == "__main__":
    main()
