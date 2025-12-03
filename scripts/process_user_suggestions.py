#!/usr/bin/env python3
"""
Process User Suggestions
Convert user suggestions into episodic memory format
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from twinself.core.config import config


def load_suggestions(suggestions_file: Path) -> list:
    """Load user suggestions from file."""
    if not suggestions_file.exists():
        print(f"No suggestions file found: {suggestions_file}")
        return []
    
    with open(suggestions_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
        except json.JSONDecodeError:
            print(f"Error reading suggestions file: {suggestions_file}")
            return []


def convert_to_episodic_format(suggestions: list) -> list:
    """
    Convert user suggestions to episodic memory format.
    
    Format:
    {
        "user_query": "question",
        "your_response": "answer"
    }
    """
    episodic_entries = []
    
    for suggestion in suggestions:
        # Only keep user_query and your_response
        entry = {
            "user_query": suggestion.get("user_query", ""),
            "your_response": suggestion.get("your_response", "")
        }
        episodic_entries.append(entry)
    
    return episodic_entries


def merge_with_existing_episodic(new_entries: list, episodic_file: Path) -> list:
    """Merge new entries with existing episodic data."""
    if episodic_file.exists():
        with open(episodic_file, 'r', encoding='utf-8') as f:
            try:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []
    
    # Check for duplicates based on user_query
    existing_queries = {entry.get("user_query", "") for entry in existing}
    
    unique_new = []
    duplicates = 0
    
    for entry in new_entries:
        query = entry.get("user_query", "")
        if query and query not in existing_queries:
            unique_new.append(entry)
            existing_queries.add(query)
        else:
            duplicates += 1
    
    print(f"  New unique entries: {len(unique_new)}")
    print(f"  Duplicates skipped: {duplicates}")
    
    return existing + unique_new


def save_episodic_data(data: list, output_file: Path):
    """Save episodic data to file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  Saved to: {output_file}")


def archive_processed_suggestions(suggestions_file: Path):
    """Archive processed suggestions."""
    if not suggestions_file.exists():
        return
    
    archive_dir = suggestions_file.parent / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file = archive_dir / f"user_suggestions_{timestamp}.json"
    
    # Copy to archive
    with open(suggestions_file, 'r') as src:
        with open(archive_file, 'w') as dst:
            dst.write(src.read())
    
    print(f"  Archived to: {archive_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Process user suggestions into episodic memory"
    )
    parser.add_argument(
        '--suggestions-file',
        default='episodic_data/user_suggestions.json',
        help='Path to user suggestions file'
    )
    parser.add_argument(
        '--output-file',
        default='episodic_data/user_feedback_examples.json',
        help='Output episodic data file'
    )
    parser.add_argument(
        '--merge',
        action='store_true',
        help='Merge with existing episodic data'
    )
    parser.add_argument(
        '--archive',
        action='store_true',
        help='Archive processed suggestions'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    
    args = parser.parse_args()
    
    print("Processing User Suggestions")
    print("=" * 60)
    
    suggestions_file = Path(args.suggestions_file)
    output_file = Path(args.output_file)
    
    # Load suggestions
    print(f"\nLoading suggestions from: {suggestions_file}")
    suggestions = load_suggestions(suggestions_file)
    
    if not suggestions:
        print("No suggestions to process.")
        return
    
    print(f"Found {len(suggestions)} suggestion(s)")
    
    # Convert to episodic format
    print("\nConverting to episodic format...")
    episodic_entries = convert_to_episodic_format(suggestions)
    
    # Show preview
    print("\nPreview of first entry:")
    print("-" * 60)
    if episodic_entries:
        print(json.dumps(episodic_entries[0], indent=2, ensure_ascii=False))
    print("-" * 60)
    
    if args.dry_run:
        print("\nDry run mode - no files will be modified")
        print(f"Would save {len(episodic_entries)} entries to: {output_file}")
        if args.archive:
            print(f"Would archive suggestions to: episodic_data/archive/")
        return
    
    # Merge with existing if requested
    if args.merge:
        print(f"\nMerging with existing data in: {output_file}")
        episodic_entries = merge_with_existing_episodic(episodic_entries, output_file)
    
    # Save episodic data
    print(f"\nSaving episodic data...")
    save_episodic_data(episodic_entries, output_file)
    
    # Archive if requested
    if args.archive:
        print(f"\nArchiving processed suggestions...")
        archive_processed_suggestions(suggestions_file)
        
        # Clear the suggestions file
        with open(suggestions_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        print(f"  Cleared: {suggestions_file}")
    
    print("\n" + "=" * 60)
    print("Processing completed successfully!")
    print("\nNext steps:")
    print("  1. Review the episodic data file")
    print("  2. Run smart rebuild to update memory:")
    print(f"     python scripts/smart_rebuild.py --create-version")


if __name__ == "__main__":
    main()
