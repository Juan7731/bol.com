# Automated Scheduling Setup Guide

The Bol.com order processing system supports automated scheduling with up to 4 processing times per day.

## Current Configuration

Default processing times (configured in `config.py`):
- **08:00** (8:00 AM)
- **15:01** (3:01 PM)
- Slot 3: Empty (can be configured)
- Slot 4: Empty (can be configured)

## Option 1: Python Scheduler (Long-Running Process)

Run the scheduler as a continuous process that checks times and runs automatically:

```bash
python run_scheduler.py
```

Or:

```bash
python order_processing.py --scheduler
```

**Pros:**
- Simple to start
- No system configuration needed
- Easy to test

**Cons:**
- Requires process to run continuously
- If process crashes, scheduling stops
- Uses system resources 24/7

**For Production:**
- Use a process manager like `systemd` (Linux) or `nssm` (Windows)
- Or run in a screen/tmux session

## Option 2: System Cron / Task Scheduler (Recommended)

Use your operating system's built-in scheduler to run the script at specific times.

### Linux / Unix (Cron)

Edit crontab:
```bash
crontab -e
```

Add these lines:
```cron
# Bol.com order processing - 08:00 and 15:01 daily
0 8 * * * /usr/bin/python /path/to/order_processing.py
1 15 * * * /usr/bin/python /path/to/order_processing.py
```

**Note:** Replace `/path/to/` with the actual path to your script.

### Windows Task Scheduler

1. Open **Task Scheduler** (taskschd.msc)
2. Create **Basic Task**
3. Set trigger:
   - **Daily** at **08:00**
   - **Daily** at **15:01**
4. Set action:
   - **Start a program**
   - Program: `python.exe` (or full path to Python)
   - Arguments: `order_processing.py`
   - Start in: `C:\Users\Lucky\Pictures\Bol` (your script directory)

### Windows PowerShell (One-time Setup)

Run this in PowerShell as Administrator:

```powershell
# Create scheduled task for 08:00
$action1 = New-ScheduledTaskAction -Execute "python.exe" -Argument "order_processing.py" -WorkingDirectory "C:\Users\Lucky\Pictures\Bol"
$trigger1 = New-ScheduledTaskTrigger -Daily -At "08:00"
Register-ScheduledTask -TaskName "BolOrderProcessing-0800" -Action $action1 -Trigger $trigger1 -Description "Bol.com order processing at 08:00"

# Create scheduled task for 15:01
$action2 = New-ScheduledTaskAction -Execute "python.exe" -Argument "order_processing.py" -WorkingDirectory "C:\Users\Lucky\Pictures\Bol"
$trigger2 = New-ScheduledTaskTrigger -Daily -At "15:01"
Register-ScheduledTask -TaskName "BolOrderProcessing-1501" -Action $action2 -Trigger $trigger2 -Description "Bol.com order processing at 15:01"
```

## Option 3: Server Deployment (TransIP)

For the production server at `/data/sites/web/trivium-ecommercecom/FTP/Script/`:

### Using Cron (Linux Server)

```bash
# Edit crontab
crontab -e

# Add these lines:
0 8 * * * /usr/bin/python3 /data/sites/web/trivium-ecommercecom/FTP/Script/order_processing.py >> /data/sites/web/trivium-ecommercecom/FTP/Script/logs/processing.log 2>&1
1 15 * * * /usr/bin/python3 /data/sites/web/trivium-ecommercecom/FTP/Script/order_processing.py >> /data/sites/web/trivium-ecommercecom/FTP/Script/logs/processing.log 2>&1
```

### Using systemd Service (Linux Server)

Create `/etc/systemd/system/bol-order-processor.service`:

```ini
[Unit]
Description=Bol.com Order Processing Scheduler
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/data/sites/web/trivium-ecommercecom/FTP/Script
ExecStart=/usr/bin/python3 /data/sites/web/trivium-ecommercecom/FTP/Script/run_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable bol-order-processor
sudo systemctl start bol-order-processor
```

## Modifying Processing Times

Edit `config.py`:

```python
PROCESS_TIMES = [
    "08:00",   # First time
    "15:01",   # Second time
    "12:00",   # Third time (optional)
    "18:00",   # Fourth time (optional)
]
```

Leave empty strings `""` for unused slots.

## Testing

Test the scheduler manually:

```bash
# Run once immediately
python order_processing.py

# Run scheduler (will check times every 30 seconds)
python run_scheduler.py
```

## Monitoring

Check logs to verify scheduled runs:
- Console output (if running interactively)
- Log files (if configured)
- Email notifications (sent after each run)

## Troubleshooting

**Scheduler not running:**
- Check if Python process is running
- Verify `PROCESS_TIMES` in `config.py` are valid
- Check system logs for errors

**Times not triggering:**
- Verify time format is `HH:MM` (24-hour)
- Check system timezone matches your expectations
- Ensure script is running at the scheduled time

**Permission issues:**
- Ensure script has write permissions for `batches/` directory
- Verify SFTP credentials are correct
- Check email SMTP settings

