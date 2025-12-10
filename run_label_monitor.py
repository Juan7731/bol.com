"""
Quick runner script to start the label PDF monitor
This will watch the 'label' folder and automatically upload new PDF files to FTP
"""

import sys
from label_uploader import monitor_label_folder, upload_all_labels

def main():
    print("\n" + "="*80)
    print("LABEL PDF AUTO-UPLOADER")
    print("="*80)
    print("\nOptions:")
    print("  1. Start monitoring (upload new files only)")
    print("  2. Upload all existing files, then start monitoring")
    print("  3. Upload all existing files only (no monitoring)")
    print("  4. Exit")
    print("="*80)
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        print("\n✅ Starting monitor (new files only)...\n")
        monitor_label_folder(check_interval=5, upload_existing=False)
    elif choice == "2":
        print("\n✅ Uploading existing files, then starting monitor...\n")
        monitor_label_folder(check_interval=5, upload_existing=True)
    elif choice == "3":
        print("\n✅ Uploading all existing files...\n")
        upload_all_labels()
    elif choice == "4":
        print("\n👋 Goodbye!\n")
        sys.exit(0)
    else:
        print("\n❌ Invalid choice. Please run again and select 1-4.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user. Goodbye!\n")
        sys.exit(0)

