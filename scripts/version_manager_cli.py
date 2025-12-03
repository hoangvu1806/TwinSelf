import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from twinself.core.version_manager import VersionManager


def cmd_list(args):
    """List all versions."""
    vm = VersionManager()
    versions = vm.list_versions()
    
    if not versions:
        print("No versions found.")
        return
    
    print("\nMemory Versions:")
    print("=" * 80)
    
    for v in reversed(versions):
        status = "ACTIVE" if v.is_active else "Inactive"
        print(f"\n{status} {v.version_id}")
        print(f"  Timestamp: {v.timestamp}")
        print(f"  Collections:")
        for coll, count in v.collections.items():
            print(f"    - {coll}: {count} points")
        if v.metadata:
            print(f"  Metadata: {v.metadata}")


def cmd_active(args):
    vm = VersionManager()
    active = vm.get_active_version()
    
    if not active:
        print("No active version found.")
        return
    
    print(f"\nActive Version: {active.version_id}")
    print(f"Timestamp: {active.timestamp}")
    print(f"Collections:")
    for coll, count in active.collections.items():
        print(f"  - {coll}: {count} points")


def cmd_rollback(args):
    vm = VersionManager()
    
    if not args.version_id:
        print("Error: version_id required")
        return
    
    print(f"\nRolling back to version: {args.version_id}")
    
    if args.data_only:
        print("This will restore Qdrant data from snapshot.")
    else:
        print("This will restore both data and version pointer.")
    
    # Check if snapshot exists
    snapshots = vm.list_snapshots()
    if args.version_id not in snapshots:
        print(f"\nWarning: No snapshot found for {args.version_id}")
        print("Available snapshots:", snapshots)
        if not args.yes:
            confirm = input("Continue with metadata-only rollback? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Rollback cancelled.")
                return
    
    if not args.yes:
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Rollback cancelled.")
            return
    
    restore_data = not args.metadata_only
    success = vm.rollback_to_version(args.version_id, restore_data=restore_data)
    
    if success:
        print("\nRollback successful!")
        print("IMPORTANT: You MUST restart the server to use the rolled-back version!")
        print("\nNext steps:")
        print("  1. Stop server: Ctrl+C")
        print("  2. Restart: python simple_server.py")
    else:
        print("\nRollback failed.")


def cmd_diff(args):
    vm = VersionManager()
    
    if not args.version1 or not args.version2:
        print("Error: Both version1 and version2 required")
        return
    
    diff = vm.get_version_diff(args.version1, args.version2)
    
    if not diff:
        print("Error: One or both versions not found")
        return
    
    print(f"\nDiff: {args.version1} → {args.version2}")
    print("=" * 80)
    
    if diff['collection_changes']:
        print("\nCollection Changes:")
        for coll, changes in diff['collection_changes'].items():
            delta = changes['delta']
            sign = '+' if delta > 0 else ''
            print(f"  {coll}: {changes['before']} → {changes['after']} ({sign}{delta})")
    else:
        print("\nNo collection changes")
    
    if diff['data_hash_changes']:
        print("\nData Changes:")
        for data_type, changes in diff['data_hash_changes'].items():
            print(f"  {data_type}: {changes['before']}... → {changes['after']}...")
    else:
        print("\nNo data changes")


def cmd_snapshots(args):
    vm = VersionManager()
    snapshots = vm.list_snapshots()
    
    if not snapshots:
        print("No snapshots found.")
        return
    
    print("\nAvailable Snapshots:")
    print("=" * 80)
    
    total_size = 0
    for snapshot in sorted(snapshots, reverse=True):
        size = vm.get_snapshot_size(snapshot)
        total_size += size
        size_mb = size / (1024 * 1024)
        print(f"  {snapshot}: {size_mb:.2f} MB")
    
    print(f"\nTotal: {len(snapshots)} snapshots, {total_size / (1024 * 1024):.2f} MB")


def cmd_cleanup(args):
    vm = VersionManager()
    
    keep = args.keep if args.keep else 5
    
    print(f"\nCleaning up old snapshots (keeping last {keep})...")
    
    if not args.yes:
        snapshots = vm.list_snapshots()
        if len(snapshots) <= keep:
            print(f"Only {len(snapshots)} snapshots exist. Nothing to clean.")
            return
        
        print(f"This will delete {len(snapshots) - keep} snapshots.")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cleanup cancelled.")
            return
    
    deleted = vm.cleanup_old_snapshots(keep_last=keep)
    print(f"Deleted {deleted} old snapshots")


def main():
    parser = argparse.ArgumentParser(description="TwinSelf Version Manager")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    subparsers.add_parser('list', help='List all versions')
    
    # Active command
    subparsers.add_parser('active', help='Show active version')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to version')
    rollback_parser.add_argument('version_id', help='Version ID to rollback to')
    rollback_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    rollback_parser.add_argument('--metadata-only', action='store_true', help='Only update version pointer, do not restore data')
    rollback_parser.add_argument('--data-only', action='store_true', help='Only restore data, do not update version pointer')
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Compare two versions')
    diff_parser.add_argument('version1', help='First version ID')
    diff_parser.add_argument('version2', help='Second version ID')
    
    # Snapshots command
    subparsers.add_parser('snapshots', help='List all snapshots')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old snapshots')
    cleanup_parser.add_argument('--keep', type=int, default=5, help='Number of snapshots to keep (default: 5)')
    cleanup_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        'list': cmd_list,
        'active': cmd_active,
        'rollback': cmd_rollback,
        'diff': cmd_diff,
        'snapshots': cmd_snapshots,
        'cleanup': cmd_cleanup
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
