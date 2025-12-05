import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from twinself.core.config import config
from twinself.core.incremental_builder import IncrementalBuilder
from twinself.core.version_manager import VersionManager
from twinself import build_semantic_memory, build_episodic_memory, build_procedural_memory
from twinself.utils.generate_rules_from_episodic_data import (
    load_episodic_examples,
    generate_procedural_rules,
    save_generated_rules
)
from qdrant_client import QdrantClient


def get_collection_stats(client: QdrantClient) -> dict:
    """Get statistics for all collections."""
    stats = {}
    for collection in [
        config.semantic_memory_collection,
        config.episodic_memory_collection,
        config.procedural_memory_collection
    ]:
        try:
            count = client.count(collection_name=collection).count
            stats[collection] = count
        except Exception:
            stats[collection] = 0
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Smart rebuild - only updates changed memories"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild all memories even if no changes detected'
    )
    parser.add_argument(
        '--skip-procedural-gen',
        action='store_true',
        help='Skip auto-generation of procedural rules'
    )
    parser.add_argument(
        '--create-version',
        action='store_true',
        help='Create version snapshot after rebuild'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be rebuilt without actually rebuilding'
    )
    
    args = parser.parse_args()
    
    print("TwinSelf Smart Rebuild Pipeline")
    print("=" * 60)
    
    # Initialize managers
    builder = IncrementalBuilder()
    version_manager = VersionManager()
    
    # Check changes
    print("\nAnalyzing changes...")
    semantic_changes = builder.get_change_summary(config.semantic_data_dir, 'semantic')
    episodic_changes = builder.get_change_summary(config.episodic_data_dir, 'episodic')
    procedural_changes = builder.get_change_summary(config.procedural_data_dir, 'procedural')
    system_prompt_changes = builder.get_change_summary(config.system_prompts_dir, 'system_prompt')
    
    print(f"\n  Semantic Memory:  {semantic_changes['total_changes']} changes")
    print(f"    - Added:       {semantic_changes['added']}")
    print(f"    - Modified:    {semantic_changes['modified']}")
    print(f"    - Deleted:     {semantic_changes['deleted']}")
    
    print(f"\n  Episodic Memory:  {episodic_changes['total_changes']} changes")
    print(f"    - Added:       {episodic_changes['added']}")
    print(f"    - Modified:    {episodic_changes['modified']}")
    print(f"    - Deleted:     {episodic_changes['deleted']}")
    
    print(f"\n  Procedural Memory: {procedural_changes['total_changes']} changes")
    print(f"    - Added:       {procedural_changes['added']}")
    print(f"    - Modified:    {procedural_changes['modified']}")
    print(f"    - Deleted:     {procedural_changes['deleted']}")
    
    print(f"\n  System Prompt:    {system_prompt_changes['total_changes']} changes")
    print(f"    - Added:       {system_prompt_changes['added']}")
    print(f"    - Modified:    {system_prompt_changes['modified']}")
    print(f"    - Deleted:     {system_prompt_changes['deleted']}")
    
    total_changes = (
        semantic_changes['total_changes'] +
        episodic_changes['total_changes'] +
        procedural_changes['total_changes'] +
        system_prompt_changes['total_changes']
    )
    
    if not args.force and total_changes == 0:
        print("\nNo changes detected. All memories are up to date!")
        return
    
    if args.dry_run:
        print("\nDry run mode - showing what would be rebuilt:")
        if semantic_changes['total_changes'] > 0 or args.force:
            print("Semantic memory would be rebuilt")
        if episodic_changes['total_changes'] > 0 or args.force:
            print("Episodic memory would be rebuilt")
        if (episodic_changes['total_changes'] > 0 or args.force) and not args.skip_procedural_gen:
            print("Procedural rules would be regenerated")
        if procedural_changes['total_changes'] > 0 or args.force:
            print("Procedural memory would be rebuilt")
        return
    
    print("\n🔨 Starting rebuild process...")
    
    # Rebuild semantic memory
    if semantic_changes['total_changes'] > 0 or args.force:
        print("\nRebuilding semantic memory...")
        build_semantic_memory()
        builder.update_cache(config.semantic_data_dir, 'semantic')
        print("Semantic memory updated")
    else:
        print("\nSkipping semantic memory (no changes)")
    
    # Rebuild episodic memory
    if episodic_changes['total_changes'] > 0 or args.force:
        print("\nRebuilding episodic memory...")
        build_episodic_memory()
        builder.update_cache(config.episodic_data_dir, 'episodic')
        print("Episodic memory updated")
        
        # Auto-generate procedural rules if episodic changed
        if not args.skip_procedural_gen:
            print("\nAuto-generating procedural rules from episodic data...")
            try:
                examples = load_episodic_examples(config.episodic_data_dir)
                rules = generate_procedural_rules(examples)
                if rules:
                    save_generated_rules(rules, config.procedural_data_dir)
                    print("Procedural rules generated")
                    # Mark procedural as changed
                    procedural_changes['total_changes'] += 1
            except Exception as e:
                print(f"Warning: Failed to generate procedural rules: {e}")
    else:
        print("\nSkipping episodic memory (no changes)")
    
    # Rebuild procedural memory
    if procedural_changes['total_changes'] > 0 or args.force:
        print("\nRebuilding procedural memory...")
        build_procedural_memory()
        builder.update_cache(config.procedural_data_dir, 'procedural')
        print("Procedural memory updated")
    else:
        print("\nSkipping procedural memory (no changes)")

    if args.create_version:
        print("\nCreating version snapshot...")
        client = QdrantClient(path=config.qdrant_local_path, prefer_grpc=False)
        stats = get_collection_stats(client)
        
        data_hash = {
            'semantic': builder._compute_directory_hash(config.semantic_data_dir),
            'episodic': builder._compute_directory_hash(config.episodic_data_dir),
            'procedural': builder._compute_directory_hash(config.procedural_data_dir),
            'system_prompt': builder._compute_directory_hash(config.system_prompts_dir)
        }
        
        # Find active system prompt
        system_prompt_file = None
        prompts_dir = Path(config.system_prompts_dir)
        if prompts_dir.exists():
            # Look for default_prompt.md or any .md file
            prompt_files = list(prompts_dir.glob('*.md'))
            if prompt_files:
                system_prompt_file = str(prompt_files[0])  # Use first found
        
        version_id = version_manager.create_version(
            collections=stats,
            data_hash=data_hash,
            metadata={
                'changes': {
                    'semantic': semantic_changes,
                    'episodic': episodic_changes,
                    'procedural': procedural_changes,
                    'system_prompt': system_prompt_changes
                }
            }
        )
        
        # Update version with system prompt file
        for v in version_manager.versions:
            if v.version_id == version_id:
                v.system_prompt_file = system_prompt_file
                break
        version_manager._save_registry()
        
        print(f"Version created: {version_id}")
        if system_prompt_file:
            print(f"System prompt tracked: {system_prompt_file}")
        
        # Create full snapshot of Qdrant data and system prompt
        print(f"Creating data snapshot...")
        if version_manager.create_snapshot(version_id, system_prompt_file):
            snapshot_size = version_manager.get_snapshot_size(version_id)
            print(f"Snapshot saved: {snapshot_size / (1024*1024):.2f} MB")
        else:
            print(f"Warning: Failed to create snapshot")
    
    print("\n" + "=" * 60)
    print("Smart rebuild completed successfully!")
    print("\nNext steps:")
    print("  1. Test the chatbot: python -m twinself.chatbot")
    print("  2. Restart server: python advanced_server.py")
    if args.create_version:
        print("  3. View versions: python scripts/version_manager_cli.py list")


if __name__ == "__main__":
    main()
