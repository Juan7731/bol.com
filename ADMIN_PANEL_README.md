# Admin Panel Documentation

Complete HTML/PHP admin interface for configuring the Bol.com order processing system.

---

## 🎯 Features

### Authentication
- ✅ **Username**: `admin`
- ✅ **Password**: `root`
- ✅ Session-based authentication
- ✅ Automatic logout
- ✅ Secure login page

### Configuration Management
- ✅ **Time Slot Configuration** (up to 4 daily time slots)
- ✅ **Weekly Schedule** (enable/disable specific days)
- ✅ **Real-time Updates** (changes take effect on next scheduled run)
- ✅ **Validation** (time format checking)

---

## 🚀 Quick Start

### 1. Access the Admin Panel

**URL**: `http://your-server/admin/`

This will redirect to the login page.

### 2. Login

- **Username**: `admin`
- **Password**: `root`

### 3. Configure Processing

1. **Set Time Slots** (up to 4)
   - Default: 08:30 and 15:01
   - Optional slots 3 and 4
   - Empty = disabled

2. **Select Active Days**
   - Check days when processing should run
   - Uncheck days to disable processing

3. **Save Configuration**
   - Click "Save Configuration"
   - Changes take effect immediately

---

## 📁 File Structure

```
admin/
├── login.php              # Login page
├── index.php              # Main configuration page
├── auth.php               # Authentication check
├── logout.php             # Logout handler
├── config.php             # Configuration manager
└── .htaccess             # Security settings

admin_config.json          # Configuration storage (auto-created)
admin_config_reader.py     # Python config reader
run_scheduler_with_admin_config.py  # Scheduler with admin config
```

---

## ⚙️ Configuration Details

### Time Slot Configuration

**Purpose**: Define when the system should automatically process orders

**Time Slots**:
1. **Slot 1** (Required): Default 08:30
2. **Slot 2** (Required): Default 15:01
3. **Slot 3** (Optional): Custom time or empty
4. **Slot 4** (Optional): Custom time or empty

**What Happens at Each Time Slot**:
- ✅ Fetch orders from Bol.com API
- ✅ Generate CSV batch files
- ✅ Create shipping label PDFs
- ✅ Upload files to FTP
- ✅ Send email notifications

**Format**: HH:MM (24-hour format)
**Examples**: `08:30`, `15:01`, `20:00`

**Note**: Empty slots are ignored

### Weekly Schedule Configuration

**Purpose**: Control which days processing should run

**Days Available**:
- Monday
- Tuesday
- Wednesday
- Thursday
- Friday
- Saturday
- Sunday

**Default Configuration**:
- ✅ Monday - Friday: Enabled
- ❌ Saturday - Sunday: Disabled

**Important**: 
- If a day is unchecked, processing will NOT run on that day
- This overrides time slot configuration
- Useful for holidays, weekends, maintenance days

---

## 🖥️ Admin Interface

### Login Page

**Features**:
- Clean, modern design
- Purple gradient background
- Secure session handling
- Error messages for invalid credentials

**Screenshot Description**:
```
┌────────────────────────────────┐
│         🔐                     │
│      Admin Login               │
│  Bol.com Order Processing      │
│                                │
│  Username: [____________]      │
│  Password: [____________]      │
│                                │
│  [        Login        ]       │
└────────────────────────────────┘
```

### Configuration Page

**Features**:
- Professional dashboard layout
- Header with user info and logout button
- Time slot input fields
- Day checkbox grid
- Save/Reset buttons
- Success/Error notifications
- Last updated timestamp

**Layout**:
```
┌────────────────────────────────────────┐
│ ⚙️ Admin Panel            👤 admin  🚪│
├────────────────────────────────────────┤
│                                        │
│ 🤖 Automatic Processing Configuration │
│                                        │
│ ⏰ Time Slot Configuration             │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│ │08:30 │ │15:01 │ │      │ │      │  │
│ └──────┘ └──────┘ └──────┘ └──────┘  │
│                                        │
│ 📅 Weekly Schedule                     │
│ [✓] Mon [✓] Tue [✓] Wed [✓] Thu      │
│ [✓] Fri [ ] Sat [ ] Sun               │
│                                        │
│ [💾 Save Configuration] [↺ Reset]    │
└────────────────────────────────────────┘
```

---

## 🔧 Setup Instructions

### Prerequisites

1. **PHP 7.0+** with session support
2. **Web server** (Apache/Nginx) with PHP
3. **Write permissions** for config file creation

### Installation

**1. Copy Admin Files**

Copy the `admin/` directory to your web server:
```bash
# Example for local PHP server
cp -r admin/ C:/Users/Lucky/Pictures/Bol/admin/
```

**2. Set Permissions**

Ensure the web server can write config files:
```bash
# Windows
icacls "C:\Users\Lucky\Pictures\Bol" /grant Users:F

# Linux/Mac
chmod 755 admin/
chmod 666 admin_config.json  # Will be created automatically
```

**3. Start Web Server**

**Option A: PHP Built-in Server (Development)**
```bash
cd C:\Users\Lucky\Pictures\Bol
php -S localhost:8080
```

Then access: `http://localhost:8080/admin/`

**Option B: Apache/Nginx (Production)**

Configure your web server to serve the Bol directory.

**4. Login**

- Navigate to `http://your-server/admin/`
- Username: `admin`
- Password: `root`

**5. Configure**

- Set time slots
- Select active days
- Save configuration

---

## 🐍 Python Integration

### Using Admin Configuration in Python

**1. Read Configuration**

```python
from admin_config_reader import AdminConfigReader

# Initialize reader
config = AdminConfigReader()

# Get processing times
times = config.get_processing_times()
# Returns: ['08:30', '15:01']

# Get weekly schedule
schedule = config.get_weekly_schedule()
# Returns: {'monday': True, 'tuesday': True, ...}

# Check if processing enabled today
if config.is_processing_enabled_today():
    print("Processing is enabled today")
```

**2. Use with Scheduler**

```python
python run_scheduler_with_admin_config.py
```

This will:
- ✅ Read configuration from admin panel
- ✅ Schedule processing at configured times
- ✅ Skip disabled days automatically
- ✅ Reload config hourly to pick up changes

---

## 📊 How It Works

### Configuration Flow

```
1. Admin accesses web interface
   ↓
2. Logs in with credentials
   ↓
3. Configures time slots and days
   ↓
4. Clicks "Save Configuration"
   ↓
5. PHP saves to admin_config.json
   ↓
6. Python scheduler reads JSON file
   ↓
7. Scheduler updates processing times
   ↓
8. System processes at configured times
```

### Configuration Storage

**File**: `admin_config.json`

**Format**:
```json
{
    "processing_times": [
        "08:30",
        "15:01",
        "",
        ""
    ],
    "weekly_schedule": {
        "monday": true,
        "tuesday": true,
        "wednesday": true,
        "thursday": true,
        "friday": true,
        "saturday": false,
        "sunday": false
    },
    "last_updated": "2025-12-10 14:30:00"
}
```

---

## 🔐 Security

### Authentication

- **Username**: Hardcoded in `login.php`
- **Password**: Hardcoded in `login.php`
- **Session**: PHP session-based authentication
- **Timeout**: Sessions expire on browser close

### File Protection

**.htaccess** settings:
- Disable directory listing
- Protect JSON files
- Security headers
- XSS protection

### Recommendations

**Production Deployment**:

1. **Change Credentials**
   ```php
   // In login.php, change these lines:
   if ($username === 'your_username' && $password === 'your_secure_password') {
   ```

2. **Use HTTPS**
   - SSL certificate required
   - Never use HTTP in production

3. **Restrict IP Access**
   ```apache
   # In .htaccess
   Order deny,allow
   Deny from all
   Allow from 192.168.1.100
   ```

4. **Database Authentication** (Optional)
   - Store credentials in database
   - Hash passwords with password_hash()

---

## 🧪 Testing

### Test Configuration

**1. Access Admin Panel**
```
http://localhost:8080/admin/
```

**2. Login**
- Username: `admin`
- Password: `root`

**3. Configure Times**
- Set times: `10:00`, `14:00`
- Enable: Monday, Tuesday
- Save configuration

**4. Test Python Reader**
```bash
python admin_config_reader.py
```

Expected output:
```
================================================================================
ADMIN CONFIGURATION
================================================================================

⏰ Processing Times:
  1. 10:00
  2. 14:00

📅 Weekly Schedule:
  Monday       ✅ Enabled
  Tuesday      ✅ Enabled
  Wednesday    ❌ Disabled
  Thursday     ❌ Disabled
  Friday       ❌ Disabled
  Saturday     ❌ Disabled
  Sunday       ❌ Disabled

🔍 Processing enabled today: Yes ✅
⏰ Next processing: Monday at 10:00
================================================================================
```

**5. Test Scheduler**
```bash
python run_scheduler_with_admin_config.py
```

Should show configured times and schedule.

---

## 📝 API Reference

### ConfigManager Class (PHP)

**Methods**:

```php
// Get all configuration
$config = $configManager->getAll();

// Get processing times
$times = $configManager->getProcessingTimes();
// Returns: ['08:30', '15:01', '', '']

// Get weekly schedule
$schedule = $configManager->getWeeklySchedule();
// Returns: ['monday' => true, 'tuesday' => true, ...]

// Update processing times
$configManager->updateProcessingTimes(['08:30', '15:01', '20:00', '']);

// Update weekly schedule
$configManager->updateWeeklySchedule([
    'monday' => 'on',
    'tuesday' => 'on',
    'wednesday' => 'on'
]);

// Save configuration
$configManager->save();

// Get last updated timestamp
$timestamp = $configManager->getLastUpdated();
```

### AdminConfigReader Class (Python)

**Methods**:

```python
# Initialize
config = AdminConfigReader()

# Get processing times (non-empty only)
times = config.get_processing_times()
# Returns: ['08:30', '15:01']

# Get weekly schedule
schedule = config.get_weekly_schedule()
# Returns: {'monday': True, 'tuesday': True, ...}

# Check if enabled today
enabled = config.is_processing_enabled_today()
# Returns: True/False

# Check if enabled for specific day
enabled = config.is_processing_enabled_for_day('monday')
# Returns: True/False

# Check if should process now
should_process = config.should_process_now()
# Returns: True/False

# Get next processing time
day, time = config.get_next_processing_time()
# Returns: ('Monday', '08:30') or (None, None)

# Reload configuration
config.reload()
```

---

## 🔄 Updating Configuration

### From Admin Panel

1. Login to admin panel
2. Change time slots or days
3. Click "Save Configuration"
4. Changes take effect on next check (within 1 hour)

### Manually (JSON File)

Edit `admin_config.json`:

```json
{
    "processing_times": [
        "09:00",
        "16:00",
        "",
        ""
    ],
    "weekly_schedule": {
        "monday": true,
        "tuesday": true,
        "wednesday": true,
        "thursday": true,
        "friday": true,
        "saturday": true,
        "sunday": false
    },
    "last_updated": "2025-12-10 15:00:00"
}
```

Save and restart scheduler.

---

## 🚨 Troubleshooting

### Issue: Cannot login

**Solutions**:
- Check username is `admin`
- Check password is `root`
- Clear browser cookies
- Check PHP session support

### Issue: Configuration not saving

**Solutions**:
- Check file permissions
- Ensure write access to directory
- Check PHP error logs

### Issue: Scheduler not using new config

**Solutions**:
- Wait up to 1 hour for auto-reload
- Or restart scheduler:
  ```bash
  # Stop with Ctrl+C, then restart
  python run_scheduler_with_admin_config.py
  ```

### Issue: Times not in correct format

**Solutions**:
- Use 24-hour format: HH:MM
- Examples: `08:30`, `15:01`, `20:00`
- Leading zeros required: `08:30` not `8:30`

---

## ✅ Summary

The admin panel provides:

- ✅ **Web-based configuration** - No code changes needed
- ✅ **Secure authentication** - Username/password protection
- ✅ **Time slot management** - Up to 4 daily processing times
- ✅ **Weekly scheduling** - Enable/disable specific days
- ✅ **Real-time updates** - Changes apply automatically
- ✅ **Python integration** - Seamless scheduler integration
- ✅ **Professional UI** - Modern, responsive design
- ✅ **Easy to use** - Intuitive interface

**Status: Production Ready! 🚀**

---

*Last updated: December 10, 2025*

