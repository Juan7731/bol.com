# Callback Status Monitor - Auto Update & Label Deletion

Automatically monitors FTP callback files and updates Bol.com orders when marked as "verzonden" (shipped), then deletes the corresponding shipping label PDFs.

---

## 🎯 What It Does

1. **Monitors**: Checks `/data/sites/web/trivium-ecommercecom/FTP/Callbacks/` every minute
2. **Reads**: Processes HTML/text files containing order IDs and status
3. **Updates**: If status = "verzonden", updates order in Bol.com API to "shipped"
4. **Deletes**: Automatically deletes the corresponding PDF label from `/FTP/Label/`
5. **Ignores**: If status = "niet verzonden", ignores the file
6. **Archives**: Moves processed callback files to `/Callbacks/processed/`

---

## 🚀 Quick Start

### Option 1: Continuous Monitoring (Recommended)

**Run every minute automatically:**
```bash
python run_callback_monitor.py
```

This will:
- Check for new callback files every 60 seconds
- Process them automatically
- Run until you press Ctrl+C

### Option 2: Single Check

**Run one check and exit:**
```bash
python run_callback_monitor.py once
```

### Option 3: Custom Interval

**Run with custom check interval (e.g., every 30 seconds):**
```bash
python run_callback_monitor.py monitor 30
```

### Option 4: Direct Execution

**Use the original callback handler:**
```bash
python status_callback_handler.py
```

---

## 📋 How It Works

### Process Flow

```
1. Monitor detects callback file in /FTP/Callbacks/
   ↓
2. Parse file to extract:
   - Order ID (e.g., "A000C2F77M")
   - Status ("verzonden" or "niet verzonden")
   ↓
3. If status = "verzonden":
   a. Update order in Bol.com API → Mark as shipped
   b. Delete label PDF from /FTP/Label/
   c. Archive callback file to /Callbacks/processed/
   ↓
4. If status = "niet verzonden":
   - Ignore (do nothing)
   - Archive callback file
```

### Callback File Format

The system expects callback files containing:
- **Order ID**: Bol.com order identifier
- **Status**: Either "verzonden" or "niet verzonden"

Example HTML content:
```html
<html>
  <body>
    <div>Order ID: A000C2F77M</div>
    <div>Status: verzonden</div>
  </body>
</html>
```

Or simple text format:
```
Order: A000C2F77M
Status: verzonden
```

---

## 📊 Monitoring Output

### Example Output

```
================================================================================
⏰ Check #1 at 2025-12-10 14:30:00
================================================================================
Found 2 HTML files in callback directory
File callback_001.html: Order A000C2F77M, Status: verzonden
✅ Successfully updated order A000C2F77M (shipment 12345) to shipped
🗑️  Deleted label PDF: A000C2F77M.pdf
✅ Successfully processed order A000C2F77M from callback_001.html

File callback_002.html: Order B111D3G88N, Status: niet verzonden
Ignoring order B111D3G88N (not shipped)

📊 Cycle #1 Results:
   Files processed: 2
   Orders updated: 1
   Labels deleted: 1
   Ignored: 1
   Errors: 0

📈 Cumulative Totals (since start):
   Total files: 2
   Total orders updated: 1
   Total labels deleted: 1
   Total ignored: 1
   Total errors: 0

⏳ Next check at: 14:31:00
================================================================================
```

---

## 🔧 Configuration

All configuration is in `config.py`:

```python
# Bol.com API credentials
BOL_CLIENT_ID = "your-client-id"
BOL_CLIENT_SECRET = "your-client-secret"

# SFTP settings
SFTP_HOST = "triviu.ssh.transip.me"
SFTP_PORT = 22
SFTP_USERNAME = "trivium-ecommercecom"
SFTP_PASSWORD = "your-password"

# Directories (automatically configured)
SFTP_CALLBACK_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Callbacks"
SFTP_REMOTE_LABEL_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Label"
```

---

## 🧪 Testing

### Test Single File Processing

```bash
python run_callback_monitor.py once
```

### Test Continuous Monitoring (1 minute)

```bash
python run_callback_monitor.py monitor 60
```

### Manual Test with Python

```python
from status_callback_handler import process_callback_files

# Process all callback files once
stats = process_callback_files()
print(stats)
```

---

## 🔄 Integration Options

### Option 1: Run as Background Process

**Windows PowerShell:**
```powershell
Start-Process python -ArgumentList "run_callback_monitor.py" -WindowStyle Hidden
```

**Linux/Mac:**
```bash
nohup python run_callback_monitor.py &
```

### Option 2: Windows Task Scheduler

Create a scheduled task that runs:
- Program: `python.exe`
- Arguments: `C:\Users\Lucky\Pictures\Bol\run_callback_monitor.py`
- Trigger: At system startup
- Run whether user is logged on or not

### Option 3: Windows Service (NSSM)

```bash
# Install NSSM service
nssm install BolCallbackMonitor "C:\Path\To\Python\python.exe" "C:\Users\Lucky\Pictures\Bol\run_callback_monitor.py"

# Start service
nssm start BolCallbackMonitor

# Check status
nssm status BolCallbackMonitor
```

### Option 4: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line to run every minute
* * * * * cd /path/to/Bol && python run_callback_monitor.py once >> callback_monitor.log 2>&1
```

---

## 📝 File Structure

```
Bol/
├── status_callback_handler.py      # Core callback processing logic
├── run_callback_monitor.py         # Continuous monitoring script
├── CALLBACK_MONITOR_README.md      # This file
└── config.py                       # Configuration
```

---

## 🔍 What Gets Updated

### Bol.com API Updates

When status = "verzonden":
1. Finds the shipment ID for the order
2. Calls `update_shipment()` API endpoint
3. Marks the order as shipped in Bol.com system
4. Order status changes from "OPEN" to "SHIPPED"

### PDF Label Deletion

After successful Bol.com update:
1. Searches for PDF files in `/FTP/Label/` containing the order ID
2. Deletes all matching PDF files
3. Logs the deletion for tracking

### Callback File Archival

After processing:
1. Moves callback file to `/FTP/Callbacks/processed/`
2. Adds timestamp to filename
3. Keeps original for reference

---

## ⚠️ Important Notes

### Status Values

- **"verzonden"** → Update order + Delete label
- **"niet verzonden"** → Do nothing (ignore)

### Order ID Matching

The system looks for Bol.com order IDs in callback files:
- Typically 10+ character alphanumeric codes
- Example: `A000C2F77M`, `B111D3G88N`

### PDF Label Matching

Labels are matched by order ID in filename:
- If order ID = `A000C2F77M`
- Looks for any PDF containing `A000C2F77M` in filename
- Example: `A000C2F77M.pdf`, `label-A000C2F77M.pdf`

### Error Handling

- **SFTP connection fails**: Logs error, retries next cycle
- **Order not found**: Logs warning, continues
- **Shipment not found**: Logs warning, skips update
- **Label not found**: Logs info (not critical), continues
- **API update fails**: Logs error, does NOT delete label

---

## 🚨 Troubleshooting

### Issue: "No callback files found"
**Solution**: Check that callback files exist in `/FTP/Callbacks/` directory

### Issue: "Could not parse file"
**Solution**: Verify callback file format contains order ID and status

### Issue: "No shipment found for order"
**Solution**: Order may not have a shipment yet, or order ID is incorrect

### Issue: "SFTP connection failed"
**Solution**: Check SFTP credentials and network connectivity

### Issue: "Failed to update order"
**Solution**: Check Bol.com API credentials and order status

### Issue: "Label PDF not deleted"
**Solution**: 
- Check that PDF filename contains the order ID
- Verify SFTP write permissions to `/FTP/Label/`
- Check logs for specific error message

---

## 📊 Statistics Tracking

The monitor tracks:
- **Files processed**: Total callback files read
- **Orders updated**: Successfully marked as shipped
- **Labels deleted**: PDF labels removed
- **Ignored**: Files with "niet verzonden" status
- **Errors**: Any failures during processing

Statistics are shown:
- Per cycle (each check)
- Cumulative totals (since monitor started)

---

## 🔐 Security

- Uses existing SFTP credentials from `config.py`
- Credentials stored securely (not in version control)
- SFTP connections use SSH protocol (encrypted)
- OAuth 2.0 for Bol.com API authentication

---

## 📞 Support

### Check Logs

Monitor output shows detailed logs including:
- Connection status
- Files found
- Orders processed
- API responses
- Errors and warnings

### Manual Verification

After processing, verify:
1. **Bol.com**: Check order status in Bol.com Partner Dashboard
2. **FTP Labels**: Verify PDF was deleted from `/FTP/Label/`
3. **FTP Callbacks**: Check file was moved to `/Callbacks/processed/`

---

## ✅ Summary

The callback monitor provides:

- ✅ **Automatic monitoring** every minute (configurable)
- ✅ **Smart processing** of "verzonden" vs "niet verzonden"
- ✅ **Bol.com API integration** to update order status
- ✅ **Auto label deletion** from FTP after shipment
- ✅ **File archival** to keep processed callbacks
- ✅ **Detailed logging** for tracking and debugging
- ✅ **Error recovery** with retry on next cycle
- ✅ **Statistics tracking** for monitoring performance

**Status: Production Ready! 🚀**

---

## 🎯 Quick Commands Reference

| Action | Command |
|--------|---------|
| Start continuous monitor | `python run_callback_monitor.py` |
| Single check | `python run_callback_monitor.py once` |
| Custom interval | `python run_callback_monitor.py monitor 30` |
| Direct handler | `python status_callback_handler.py` |
| Stop monitor | Press `Ctrl+C` |

---

*Last updated: December 10, 2025*

