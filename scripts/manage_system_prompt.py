import sys
import argparse
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from twinself.core.config import config
from twinself.core.version_manager import VersionManager


def list_prompts():
    """List all available system prompts."""
    prompts_dir = Path(config.system_prompts_dir)
    
    if not prompts_dir.exists():
        print("No system prompts directory found.")
        return
    
    prompt_files = list(prompts_dir.glob('*.md'))
    
    if not prompt_files:
        print("No system prompts found.")
        return
    
    print("\nAvailable System Prompts:")
    print("=" * 80)
    
    for prompt_file in sorted(prompt_files):
        size = prompt_file.stat().st_size
        modified = datetime.fromtimestamp(prompt_file.stat().st_mtime)
        print(f"\n {prompt_file.name}")
        print(f"     Size: {size} bytes")
        print(f"     Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show first few lines
        with open(prompt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:3]
            if lines:
                print(f"     Preview: {lines[0].strip()[:60]}...")


def create_prompt(args):
    """Create a new system prompt."""
    prompts_dir = Path(config.system_prompts_dir)
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    prompt_file = prompts_dir / args.name
    
    if prompt_file.exists() and not args.force:
        print(f"Error: Prompt '{args.name}' already exists. Use --force to overwrite.")
        return
    
    if args.template:
        # Copy from template
        template_path = prompts_dir / args.template
        if not template_path.exists():
            print(f"Error: Template '{args.template}' not found.")
            return
        shutil.copy2(template_path, prompt_file)
        print(f"Created prompt '{args.name}' from template '{args.template}'")
    else:
        # Create from scratch
        default_content = f"""# System Prompt - {args.name}

## Role
Define the AI assistant's role here.

## Core Responsibilities
- Responsibility 1
- Responsibility 2

## Communication Style
Describe the communication style.

## Guidelines
- Guideline 1
- Guideline 2

## Version Info
- Version: v1.0.0
- Created: {datetime.now().strftime('%Y-%m-%d')}
- Purpose: {args.description or 'Custom system prompt'}
"""
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(default_content)
        print(f"Created new prompt: {prompt_file}")
    
    print("\nNext steps:")
    print(f"  1. Edit the prompt: {prompt_file}")
    print(f"  2. Rebuild with versioning: python scripts/smart_rebuild.py --create-version")


def show_prompt(args):
    """Show content of a system prompt."""
    prompts_dir = Path(config.system_prompts_dir)
    prompt_file = prompts_dir / args.name
    
    if not prompt_file.exists():
        print(f"Error: Prompt '{args.name}' not found.")
        return
    
    print(f"\nSystem Prompt: {args.name}")
    print("=" * 80)
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)


def diff_prompts(args):
    """Compare two system prompts."""
    prompts_dir = Path(config.system_prompts_dir)
    
    file1 = prompts_dir / args.prompt1
    file2 = prompts_dir / args.prompt2
    
    if not file1.exists():
        print(f"Error: Prompt '{args.prompt1}' not found.")
        return
    
    if not file2.exists():
        print(f"Error: Prompt '{args.prompt2}' not found.")
        return
    
    with open(file1, 'r', encoding='utf-8') as f:
        content1 = f.readlines()
    
    with open(file2, 'r', encoding='utf-8') as f:
        content2 = f.readlines()
    
    print(f"\nComparing: {args.prompt1} vs {args.prompt2}")
    print("=" * 80)
    
    # Simple line-by-line diff
    max_lines = max(len(content1), len(content2))
    differences = 0
    
    for i in range(max_lines):
        line1 = content1[i].rstrip() if i < len(content1) else ""
        line2 = content2[i].rstrip() if i < len(content2) else ""
        
        if line1 != line2:
            differences += 1
            print(f"\nLine {i+1}:")
            print(f"  - {args.prompt1}: {line1[:70]}")
            print(f"  + {args.prompt2}: {line2[:70]}")
    
    if differences == 0:
        print("\nNo differences found.")
    else:
        print(f"\nTotal differences: {differences} lines")


def restore_prompt_from_version(args):
    """Restore system prompt from a specific version."""
    vm = VersionManager()
    
    # Find version
    version = None
    for v in vm.versions:
        if v.version_id == args.version_id:
            version = v
            break
    
    if not version:
        print(f"Error: Version '{args.version_id}' not found.")
        return
    
    if not version.system_prompt_file:
        print(f"Warning: Version '{args.version_id}' has no system prompt tracked.")
        return
    
    # Check if snapshot exists
    snapshot_path = vm.snapshots_dir / args.version_id / "system_prompt.md"
    
    if not snapshot_path.exists():
        print(f"Error: No system prompt snapshot found for version '{args.version_id}'")
        return
    
    # Restore prompt
    dest_path = Path(version.system_prompt_file)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    if dest_path.exists() and not args.force:
        print(f"Error: Prompt file already exists: {dest_path}")
        print("Use --force to overwrite.")
        return
    
    shutil.copy2(snapshot_path, dest_path)
    print(f"Restored system prompt from version '{args.version_id}'")
    print(f"   Location: {dest_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage system prompts as versioned data"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List all system prompts')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new system prompt')
    create_parser.add_argument('name', help='Name of the prompt file (e.g., custom_prompt.md)')
    create_parser.add_argument('--template', help='Create from existing prompt template')
    create_parser.add_argument('--description', help='Description of the prompt')
    create_parser.add_argument('--force', action='store_true', help='Overwrite if exists')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show content of a system prompt')
    show_parser.add_argument('name', help='Name of the prompt file')
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Compare two system prompts')
    diff_parser.add_argument('prompt1', help='First prompt file')
    diff_parser.add_argument('prompt2', help='Second prompt file')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore system prompt from version')
    restore_parser.add_argument('version_id', help='Version ID to restore from')
    restore_parser.add_argument('--force', action='store_true', help='Overwrite existing prompt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        'list': lambda: list_prompts(),
        'create': lambda: create_prompt(args),
        'show': lambda: show_prompt(args),
        'diff': lambda: diff_prompts(args),
        'restore': lambda: restore_prompt_from_version(args)
    }
    
    commands[args.command]()


if __name__ == "__main__":
    main()
