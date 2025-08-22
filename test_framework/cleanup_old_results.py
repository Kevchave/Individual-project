#!/usr/bin/env python3
"""
Simple script to clean up all test result files

USAGE:
    # See what files would be deleted (dry run)
    python cleanup_old_results.py
    
    # Actually delete all test result files and config registry
    python cleanup_old_results.py --delete

PURPOSE:
    Use this when you want to rerun the entire pipeline from scratch.
    This deletes:
    - All JSON, CSV, and report files from test_results/
    - All configuration files from config_registry/
"""

import os
import sys
from pathlib import Path
import argparse

def cleanup_all_results(dry_run=True):
    """Clean up ALL test result files and config registry"""
    
    files_to_delete = []
    total_size = 0
    
    # 1. Clean up test_results directory
    results_dir = Path("test_results")
    if results_dir.exists():
        for subdir in ["json_results", "csv_results", "report_results"]:
            subdir_path = results_dir / subdir
            if not subdir_path.exists():
                continue
                
            for file_path in subdir_path.glob("*"):
                if file_path.is_file():
                    files_to_delete.append({
                        'file': file_path,
                        'size': file_path.stat().st_size,
                        'type': 'test_result'
                    })
                    total_size += file_path.stat().st_size
    
    # 2. Clean up config_registry directory
    config_dir = Path("config_registry")
    if config_dir.exists():
        for file_path in config_dir.glob("*.json"):
            if file_path.is_file():
                files_to_delete.append({
                    'file': file_path,
                    'size': file_path.stat().st_size,
                    'type': 'config'
                })
                total_size += file_path.stat().st_size
    
    if not files_to_delete:
        print("✅ No files found to delete")
        return
    
    # Sort by type and filename for better display
    files_to_delete.sort(key=lambda x: (x['type'], x['file'].name))
    
    # Group by type
    test_files = [f for f in files_to_delete if f['type'] == 'test_result']
    config_files = [f for f in files_to_delete if f['type'] == 'config']
    
    print(f"🗑️  Found {len(files_to_delete)} files to delete:")
    print("=" * 60)
    
    if test_files:
        print(f"\n📊 Test Results ({len(test_files)} files):")
        for file_info in test_files:
            size_kb = file_info['size'] / 1024
            print(f"   {file_info['file'].name} | {size_kb:.1f}KB")
    
    if config_files:
        print(f"\n⚙️  Config Registry ({len(config_files)} files):")
        for file_info in config_files:
            size_kb = file_info['size'] / 1024
            print(f"   {file_info['file'].name} | {size_kb:.1f}KB")
    
    total_size_mb = total_size / (1024 * 1024)
    print(f"\n📊 Total size to free: {total_size_mb:.1f}MB")
    
    if not dry_run:
        print(f"\n🗑️  Deleting {len(files_to_delete)} files...")
        for file_info in files_to_delete:
            file_info['file'].unlink()
            print(f"   Deleted: {file_info['file'].name}")
        print("✅ All files deleted!")
        print("💡 You can now rerun the pipeline from scratch")
    else:
        print(f"\n💡 This was a dry run. To actually delete, run with --delete")

def main():
    parser = argparse.ArgumentParser(description="Clean up all test result files")
    parser.add_argument("--delete", action="store_true", help="Actually delete files (default is dry run)")
    
    args = parser.parse_args()
    
    cleanup_all_results(not args.delete)

if __name__ == "__main__":
    main() 