# Label PDF Auto-Uploader

Automatically monitors the `label` subfolder for PDF shipping labels and uploads them to the FTP server's `label` directory when they are created.

## Features

- ✅ **Automatic Monitoring**: Watches the local `label` folder for new PDF files
- ✅ **Auto-Upload**: Uploads PDF files to FTP `/data/sites/web/trivium-ecommercecom/FTP/Label` directory
- ✅ **Batch Upload**: Can upload all existing PDF files at once
- ✅ **File Verification**: Verifies file size after upload
- ✅ **Error Handling**: Robust error handling with detailed logging
- ✅ **Auto-Directory Creation**: Creates remote FTP directory if it doesn't exist

## Quick Start

### Option 1: Interactive Menu (Recommended)

Run the interactive menu:

```bash
python run_label_monitor.py
```

This will give you options to:
1. Start monitoring (upload new files only)
2. Upload all existing files, then start monitoring
3. Upload all existing files only (no monitoring)
4. Exit

### Option 2: Direct Commands

#### Monitor for new PDF files only:
```bash
python label_uploader.py monitor
```

#### Upload all existing files first, then monitor:
```bash
python label_uploader.py monitor --upload-existing
```

#### Upload all existing PDF files (batch mode):
```bash
python label_uploader.py upload-all
```

#### Test upload a specific file:
```bash
python label_uploader.py test <filename.pdf>
```

## How It Works

1. **Monitoring**: The script checks the `label` folder every 5 seconds for new PDF files
2. **Detection**: When a new PDF is detected, it's automatically queued for upload
3. **Upload**: The file is uploaded to the FTP server at `/FTP/Label/`
4. **Verification**: The upload is verified by comparing file sizes
5. **Tracking**: Successfully uploaded files are tracked to avoid duplicate uploads

## Configuration

The configuration is in `config.py`:

```python
# Local directory where shipping label PDFs are stored
LOCAL_LABEL_DIR = "label"

# Remote FTP label directory
SFTP_REMOTE_LABEL_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Label"
```

SFTP credentials are already configured in `config.py`:
- Host: `triviu.ssh.transip.me`
- Port: `22`
- Username: `trivium-ecommercecom`

## Directory Structure

```
Bol/
├── label/                          # Local label folder
│   ├── order-123-label.pdf        # PDF files automatically uploaded
│   └── order-456-label.pdf
├── label_uploader.py              # Main uploader module
├── run_label_monitor.py           # Interactive runner script
└── config.py                      # Configuration
```

## Use Cases

### Use Case 1: Background Monitoring
Run the monitor in the background to automatically upload labels as they're created:

```bash
python label_uploader.py monitor
```

Leave this running in a terminal. Whenever a new PDF is added to the `label` folder, it will be automatically uploaded.

### Use Case 2: Batch Upload Existing Files
If you have existing PDF files that weren't uploaded yet:

```bash
python label_uploader.py upload-all
```

### Use Case 3: Initial Setup + Monitoring
Upload all existing files and then start monitoring for new ones:

```bash
python label_uploader.py monitor --upload-existing
```

### Use Case 4: Integration with Order Processing
You can integrate this with your order processing workflow by:

1. Save shipping labels to the `label` folder
2. The monitor will automatically upload them to FTP
3. Your fulfillment partner can access them from the FTP server

## Logging

The script provides detailed logging:

- `📁` Directory operations
- `🆕` New file detected
- `📤` Upload in progress
- `✅` Successful upload
- `❌` Upload error
- `🗑️` File removed from tracking

Example output:
```
================================================================================
📁 Label PDF Monitor Started
================================================================================
Local directory: label
Remote FTP directory: /data/sites/web/trivium-ecommercecom/FTP/Label
Check interval: 5 seconds
Upload existing files: False
================================================================================
Found 21 existing PDF files in label folder

🔍 Monitoring for new PDF files... (Press Ctrl+C to stop)

🆕 Detected 1 new PDF file(s)
📤 Uploading 0437fe94-fce1-452c-a294-53d2e7f6ec09.pdf to /data/sites/web/trivium-ecommercecom/FTP/Label/0437fe94-fce1-452c-a294-53d2e7f6ec09.pdf
✅ Successfully uploaded 0437fe94-fce1-452c-a294-53d2e7f6ec09.pdf (45623 bytes)
```

## Troubleshooting

### Issue: "Directory does not exist"
**Solution**: The script will automatically create the `label` folder locally if it doesn't exist.

### Issue: "SFTP connection failed"
**Solution**: Check your SFTP credentials in `config.py` and ensure you have network connectivity.

### Issue: "Permission denied" on FTP
**Solution**: Verify that your SFTP user has write permissions to `/data/sites/web/trivium-ecommercecom/FTP/Label`

### Issue: Monitor doesn't detect new files
**Solution**: 
- Ensure the file extension is `.pdf` (case-insensitive)
- Check that files are being saved to the correct `label` directory
- Try stopping and restarting the monitor

## Running as a Service (Windows)

To run the label monitor continuously as a background service on Windows:

### Option 1: Using Task Scheduler
1. Open Task Scheduler
2. Create a new task
3. Set trigger: "At system startup"
4. Set action: Run `python.exe` with arguments:
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `C:\Users\Lucky\Pictures\Bol\label_uploader.py monitor`
5. Set "Run whether user is logged on or not"

### Option 2: Using NSSM (Non-Sucking Service Manager)
1. Download NSSM from https://nssm.cc/
2. Install the service:
   ```bash
   nssm install LabelUploader "C:\Path\To\Python\python.exe" "C:\Users\Lucky\Pictures\Bol\label_uploader.py" "monitor"
   ```
3. Start the service:
   ```bash
   nssm start LabelUploader
   ```

## API Integration

You can also use the uploader functions programmatically in your Python code:

```python
from label_uploader import upload_label_pdf_to_ftp, upload_all_labels

# Upload a single file
success = upload_label_pdf_to_ftp("label/order-123.pdf")

# Upload all files in the label folder
upload_all_labels()

# Start monitoring (blocking call)
from label_uploader import monitor_label_folder
monitor_label_folder(check_interval=5, upload_existing=True)
```

## Requirements

- Python 3.7+
- paramiko (already in requirements.txt)
- SFTP access to the remote server

## Security Notes

⚠️ **Important**: The `config.py` file contains sensitive credentials. Ensure:
- It's not committed to version control (add to `.gitignore`)
- File permissions are restrictive
- Only authorized users have access to this file

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify SFTP connectivity using `verify_ftp_upload.py`
3. Test with a single file using: `python label_uploader.py test <filename>`

