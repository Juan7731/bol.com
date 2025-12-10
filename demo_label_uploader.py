"""
Demo script to show the label uploader in action
This creates a sample PDF and demonstrates the upload process
"""

import os
import time
from label_uploader import upload_label_pdf_to_ftp, LOCAL_LABEL_DIR

def create_sample_pdf(filename="demo-label.pdf"):
    """
    Create a simple PDF file for demonstration purposes.
    This creates a minimal valid PDF file.
    """
    # Minimal valid PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 55
>>
stream
BT
/F1 12 Tf
100 700 Td
(Demo Shipping Label) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
422
%%EOF
"""
    
    # Ensure directory exists
    os.makedirs(LOCAL_LABEL_DIR, exist_ok=True)
    
    # Write the PDF file
    filepath = os.path.join(LOCAL_LABEL_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(pdf_content)
    
    return filepath


def demo_upload():
    """
    Demonstrate the label upload functionality
    """
    print("\n" + "="*80)
    print("LABEL UPLOADER DEMO")
    print("="*80)
    print("\nThis demo will:")
    print("1. Create a sample PDF label file")
    print("2. Upload it to the FTP server")
    print("3. Verify the upload")
    print("\n" + "="*80)
    
    input("\nPress Enter to start the demo...")
    
    # Step 1: Create sample PDF
    print("\n📄 Step 1: Creating sample PDF label...")
    filename = f"demo-label-{int(time.time())}.pdf"
    filepath = create_sample_pdf(filename)
    file_size = os.path.getsize(filepath)
    print(f"✅ Created: {filename} ({file_size} bytes)")
    print(f"   Location: {filepath}")
    
    time.sleep(1)
    
    # Step 2: Upload to FTP
    print("\n📤 Step 2: Uploading to FTP server...")
    print("   This will connect to the SFTP server and upload the file...")
    
    success = upload_label_pdf_to_ftp(filepath)
    
    if success:
        print("\n✅ Demo completed successfully!")
        print("\nThe file has been uploaded to:")
        print("   /data/sites/web/trivium-ecommercecom/FTP/Label/")
        print(f"   Filename: {filename}")
    else:
        print("\n❌ Demo upload failed. Check the logs above for details.")
    
    # Cleanup option
    print("\n" + "="*80)
    cleanup = input("\nDelete the demo file from local folder? (y/n): ").strip().lower()
    if cleanup == 'y':
        try:
            os.remove(filepath)
            print(f"✅ Deleted local file: {filename}")
        except Exception as e:
            print(f"⚠️  Could not delete file: {e}")
    else:
        print(f"ℹ️  Demo file kept: {filepath}")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nTo start monitoring for real labels:")
    print("   python run_label_monitor.py")
    print("or")
    print("   python label_uploader.py monitor")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        demo_upload()
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

