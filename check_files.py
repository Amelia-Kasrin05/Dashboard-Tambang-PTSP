# ============================================================
# DIAGNOSTIC TOOL - Check File Configuration
# ============================================================
# Save as: check_files.py
# Run with: python check_files.py

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append('.')

try:
    from onedrive_config import ONEDRIVE_FOLDER, LOCAL_FILE_NAMES, ONEDRIVE_LINKS
    print("✅ Successfully imported onedrive_config")
except ImportError as e:
    print(f"❌ Failed to import onedrive_config: {e}")
    sys.exit(1)

def format_size(bytes):
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def format_date(timestamp):
    """Format timestamp to readable date"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def check_files():
    """Main diagnostic function"""
    print("\n" + "="*70)
    print("🔍 DASHBOARD TAMBANG - FILE DIAGNOSTIC TOOL")
    print("="*70)
    
    # Check OneDrive folder
    print(f"\n📁 OneDrive Folder Configuration:")
    print(f"   Path: {ONEDRIVE_FOLDER}")
    print(f"   Exists: {'✅ YES' if os.path.exists(ONEDRIVE_FOLDER) else '❌ NO'}")
    
    if os.path.exists(ONEDRIVE_FOLDER):
        try:
            files = os.listdir(ONEDRIVE_FOLDER)
            print(f"   Files found: {len(files)}")
            print(f"   Excel files: {len([f for f in files if f.endswith('.xlsx')])}")
        except Exception as e:
            print(f"   ❌ Error reading folder: {e}")
    
    # Check OneDrive links
    print(f"\n🔗 OneDrive Links Configuration:")
    for name, link in ONEDRIVE_LINKS.items():
        if link and link.strip():
            print(f"   {name}: ✅ Configured")
        else:
            print(f"   {name}: ⚠️ Empty (will use local files)")
    
    # Check each file
    print(f"\n📄 File Status Check:")
    print("-" * 70)
    
    for file_key, paths in LOCAL_FILE_NAMES.items():
        print(f"\n📊 {file_key.upper()}:")
        
        found = False
        for i, path in enumerate(paths, 1):
            exists = os.path.exists(path)
            status = "✅" if exists else "❌"
            
            print(f"   Path {i}: {status} {path}")
            
            if exists and not found:
                found = True
                try:
                    size = os.path.getsize(path)
                    mtime = os.path.getmtime(path)
                    print(f"           📏 Size: {format_size(size)}")
                    print(f"           📅 Modified: {format_date(mtime)}")
                    
                    # Try to read Excel file
                    try:
                        import pandas as pd
                        xl = pd.ExcelFile(path)
                        print(f"           📑 Sheets: {', '.join(xl.sheet_names)}")
                        print(f"           ✅ File is readable")
                    except Exception as e:
                        print(f"           ❌ Cannot read Excel: {e}")
                        
                except Exception as e:
                    print(f"           ❌ Error: {e}")
        
        if not found:
            print(f"   ⚠️ WARNING: No valid file found for {file_key}!")
    
    # Summary
    print("\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)
    
    total_files = len(LOCAL_FILE_NAMES)
    found_files = 0
    
    for file_key, paths in LOCAL_FILE_NAMES.items():
        if any(os.path.exists(path) for path in paths):
            found_files += 1
    
    print(f"Total expected files: {total_files}")
    print(f"Files found: {found_files}")
    print(f"Files missing: {total_files - found_files}")
    
    if found_files == total_files:
        print("\n✅ ALL FILES FOUND! Dashboard should work properly.")
    elif found_files > 0:
        print(f"\n⚠️ PARTIAL: {found_files}/{total_files} files found.")
        print("   Dashboard will work with limited functionality.")
    else:
        print("\n❌ NO FILES FOUND! Dashboard will not work.")
        print("\n💡 SOLUTIONS:")
        print("   1. Make sure OneDrive is syncing properly")
        print("   2. Check if files are in correct folder")
        print(f"   3. Move Excel files to: {ONEDRIVE_FOLDER}")
        print("   4. Or create 'data' folder and copy files there")
    
    print("\n" + "="*70)
    print()

if __name__ == "__main__":
    check_files()