# Label PDF Upload Path Guide

## Current Upload Location

PDF label files are uploaded to:
```
/data/sites/web/trivium-ecommercecom/FTP/Label
```

**SFTP Server Details:**
- Host: `triviu.ssh.transip.me`
- Port: `22`
- Username: `trivium-ecommercecom`
- Remote Directory: `/data/sites/web/trivium-ecommercecom/FTP/Label`

## How to Check Uploaded Files

### Method 1: Using the Check Script

Run the check script to see all uploaded label PDFs:

```bash
python3 check_uploaded_labels.py
```

This will show:
- Total number of PDF files uploaded
- File names, sizes, and upload dates
- Connection status

### Method 2: Using SFTP Client

Connect to the SFTP server and navigate to the label directory:

```bash
sftp trivium-ecommercecom@triviu.ssh.transip.me
# Enter password when prompted
cd /data/sites/web/trivium-ecommercecom/FTP/Label
ls -lh
```

### Method 3: Using File Manager

If you have SFTP access via a file manager (like FileZilla, WinSCP, etc.):
1. Connect to `triviu.ssh.transip.me` on port 22
2. Navigate to `/data/sites/web/trivium-ecommercecom/FTP/Label`
3. You'll see all uploaded PDF files

## How to Customize Upload Path

### Option 1: Edit `config.py`

Edit the `SFTP_REMOTE_LABEL_DIR` variable in `config.py`:

```python
# Current setting:
SFTP_REMOTE_LABEL_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Label"

# Change to your custom path:
SFTP_REMOTE_LABEL_DIR = "/data/sites/web/trivium-ecommercecom/FTP/MyCustomLabelPath"
```

### Option 2: Edit `system_config.json` (Recommended)

Edit the `remote_label_dir` in `system_config.json`:

```json
{
  "ftp": {
    "host": "triviu.ssh.transip.me",
    "port": 22,
    "username": "trivium-ecommercecom",
    "password": "t99tmJ!Z8a/J",
    "remote_batch_dir": "/data/sites/web/trivium-ecommercecom/FTP/Batches",
    "remote_label_dir": "/data/sites/web/trivium-ecommercecom/FTP/MyCustomLabelPath",
    "remote_callback_dir": "/data/sites/web/trivium-ecommercecom/FTP/Callbacks"
  }
}
```

**Note:** The `system_config.json` setting takes priority over `config.py`.

## Why "No Shipping Labels Found" Message?

The log message `"ℹ️  Nenhum shipping label encontrado nos arquivos CSV"` appears when:

1. **CSV files have empty "Shipping Label" columns** - This means shipping labels weren't fetched when the CSV was generated
2. **Shipping labels need to be fetched first** - The system only uploads PDFs that are referenced in the CSV files

### To Fix This:

1. **Shipping labels must be fetched during order processing** - The system will automatically:
   - Get delivery options
   - Create shipping labels
   - Download PDF files
   - Save PDFs to local `label/` folder
   - Include label IDs in CSV "Shipping Label" column

2. **Then PDFs will be uploaded** - Once CSV files have shipping label IDs, the system will:
   - Read shipping label IDs from CSV
   - Find corresponding PDF files in `label/` folder
   - Upload them to SFTP server

## Current Status

Looking at your CSV file (`S-001.csv`), the "Shipping Label" column is empty:
```
Order ID,Shop,MP EAN,Quantity,Shipping Label,Order Time,Batch Type,Batch Number,Order Status
A000E3LUXJ,Trivium,8721161953111,1,,2026-01-22 13:15:19,Single,S-001,open
```

This means:
- ✅ Orders are being fetched correctly
- ✅ Orders are being classified correctly
- ✅ CSV files are being generated
- ❌ Shipping labels are NOT being fetched (empty column)
- ❌ PDF files are NOT being uploaded (no labels to upload)

## Next Steps

The shipping label fetching should work now that EAN extraction is fixed. When you run order processing again, it should:
1. Fetch shipping labels for FBR items
2. Download PDF files
3. Include label IDs in CSV
4. Upload PDFs to SFTP

Run order processing and check if shipping labels are now included in the CSV files.
