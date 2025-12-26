<?php
/**
 * Admin Dashboard - Automatic Processing Configuration
 */

require_once 'auth.php';
require_once 'config.php';

$configManager = new ConfigManager();
$message = '';
$message_type = '';

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        // Update processing times
        $times = [
            $_POST['time_slot_1'] ?? '',
            $_POST['time_slot_2'] ?? '',
            $_POST['time_slot_3'] ?? '',
            $_POST['time_slot_4'] ?? ''
        ];
        $configManager->updateProcessingTimes($times);
        
        // Update weekly schedule
        $schedule = [
            'monday' => $_POST['monday'] ?? '',
            'tuesday' => $_POST['tuesday'] ?? '',
            'wednesday' => $_POST['wednesday'] ?? '',
            'thursday' => $_POST['thursday'] ?? '',
            'friday' => $_POST['friday'] ?? '',
            'saturday' => $_POST['saturday'] ?? '',
            'sunday' => $_POST['sunday'] ?? ''
        ];
        $configManager->updateWeeklySchedule($schedule);
        
        // Save configuration
        if ($configManager->save()) {
            $message = 'Configuration saved successfully!';
            $message_type = 'success';
        } else {
            $message = 'Failed to save configuration';
            $message_type = 'error';
        }
    } catch (Exception $e) {
        $message = 'Error: ' . $e->getMessage();
        $message_type = 'error';
    }
}

// Load current configuration
$processing_times = $configManager->getProcessingTimes();
$weekly_schedule = $configManager->getWeeklySchedule();
$last_updated = $configManager->getLastUpdated();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Automatic Processing Configuration - Admin Panel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .user-info {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .btn-logout {
            padding: 8px 20px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-logout:hover {
            background: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.5);
        }
        
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .breadcrumb {
            margin-bottom: 20px;
            color: #666;
            font-size: 14px;
        }
        
        .breadcrumb a {
            color: #667eea;
            text-decoration: none;
        }
        
        .breadcrumb a:hover {
            text-decoration: underline;
        }
        
        .alert {
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            margin-bottom: 30px;
            overflow: hidden;
        }
        
        .card-header {
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .card-header h2 {
            font-size: 20px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-header p {
            margin-top: 8px;
            color: #666;
            font-size: 14px;
        }
        
        .card-body {
            padding: 30px;
        }
        
        .form-section {
            margin-bottom: 40px;
        }
        
        .form-section:last-child {
            margin-bottom: 0;
        }
        
        .form-section-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .form-section-description {
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        
        .time-slots-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .time-slot {
            display: flex;
            flex-direction: column;
        }
        
        .time-slot label {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .time-slot input[type="time"] {
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .time-slot input[type="time"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .time-slot-hint {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
        }
        
        .weekly-schedule {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
        }
        
        .day-checkbox {
            position: relative;
        }
        
        .day-checkbox input[type="checkbox"] {
            position: absolute;
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .day-checkbox label {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 18px;
            background: #f8f9fa;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
            color: #666;
        }
        
        .day-checkbox input[type="checkbox"]:checked + label {
            background: #e8f0fe;
            border-color: #667eea;
            color: #667eea;
        }
        
        .day-checkbox label::before {
            content: '';
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #ccc;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .day-checkbox input[type="checkbox"]:checked + label::before {
            background: #667eea;
            border-color: #667eea;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='white' d='M4.5 9L1.5 6l.7-.7L4.5 7.6 9.8 2.3l.7.7z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: center;
        }
        
        .form-actions {
            display: flex;
            gap: 15px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            margin-top: 40px;
        }
        
        .btn {
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #f8f9fa;
            color: #666;
            border: 2px solid #e0e0e0;
        }
        
        .btn-secondary:hover {
            background: #e9ecef;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        
        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(40, 167, 69, 0.4);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white;
        }
        
        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(220, 53, 69, 0.4);
        }
        
        .monitor-control {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .monitor-status {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 16px;
            font-weight: 600;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        
        .status-dot.status-online {
            background: #28a745;
            box-shadow: 0 0 8px rgba(40, 167, 69, 0.6);
        }
        
        .status-dot.status-offline {
            background: #dc3545;
        }
        
        .status-dot.status-unknown {
            background: #ffc107;
        }
        
        .monitor-actions {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .info-box {
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 16px 20px;
            border-radius: 4px;
            margin-top: 20px;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .info-box strong {
            color: #2980b9;
        }
        
        .footer {
            max-width: 1200px;
            margin: 40px auto 20px;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 13px;
        }
        
        .icon {
            font-size: 24px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>⚙️ Admin Panel</h1>
            <div class="header-right">
                <div class="user-info">
                    👤 Logged in as: <strong>admin</strong>
                </div>
                <a href="logout.php" class="btn-logout">Logout</a>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="breadcrumb">
            🏠 <a href="index.php">Home</a> / Automatic Processing Configuration
        </div>
        
        <?php if ($message): ?>
            <div class="alert alert-<?php echo $message_type; ?>">
                <?php if ($message_type === 'success'): ?>
                    ✅
                <?php else: ?>
                    ⚠️
                <?php endif; ?>
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>
        
        <div class="card">
            <div class="card-header">
                <h2>
                    <span class="icon">🤖</span>
                    Automatic Processing Configuration
                </h2>
                <p>Configure when the system should automatically process orders, generate CSV files, and create shipping labels</p>
                <?php if ($last_updated !== 'Never'): ?>
                    <p style="margin-top: 12px; color: #999;">
                        <em>Last updated: <?php echo htmlspecialchars($last_updated); ?></em>
                    </p>
                <?php endif; ?>
            </div>
            
            <div class="card-body">
                <form method="POST" action="">
                    <!-- Time Slot Configuration -->
                    <div class="form-section">
                        <div class="form-section-title">
                            ⏰ Time Slot Configuration
                        </div>
                        <div class="form-section-description">
                            Configure up to four daily time slots for automatic processing. The system will:
                            <ul style="margin-left: 20px; margin-top: 8px;">
                                <li>Fetch orders from Bol.com API</li>
                                <li>Generate CSV batch files</li>
                                <li>Create shipping label PDFs</li>
                                <li>Upload files to FTP</li>
                                <li>Send email notifications</li>
                            </ul>
                        </div>
                        
                        <div class="time-slots-grid">
                            <div class="time-slot">
                                <label for="time_slot_1">Time Slot 1 *</label>
                                <input 
                                    type="time" 
                                    id="time_slot_1" 
                                    name="time_slot_1" 
                                    value="<?php echo htmlspecialchars($processing_times[0]); ?>"
                                >
                                <span class="time-slot-hint">Default: 08:30</span>
                            </div>
                            
                            <div class="time-slot">
                                <label for="time_slot_2">Time Slot 2 *</label>
                                <input 
                                    type="time" 
                                    id="time_slot_2" 
                                    name="time_slot_2" 
                                    value="<?php echo htmlspecialchars($processing_times[1]); ?>"
                                >
                                <span class="time-slot-hint">Default: 15:01</span>
                            </div>
                            
                            <div class="time-slot">
                                <label for="time_slot_3">Time Slot 3 (Optional)</label>
                                <input 
                                    type="time" 
                                    id="time_slot_3" 
                                    name="time_slot_3" 
                                    value="<?php echo htmlspecialchars($processing_times[2]); ?>"
                                >
                                <span class="time-slot-hint">Leave empty to disable</span>
                            </div>
                            
                            <div class="time-slot">
                                <label for="time_slot_4">Time Slot 4 (Optional)</label>
                                <input 
                                    type="time" 
                                    id="time_slot_4" 
                                    name="time_slot_4" 
                                    value="<?php echo htmlspecialchars($processing_times[3]); ?>"
                                >
                                <span class="time-slot-hint">Leave empty to disable</span>
                            </div>
                        </div>
                        
                        <div class="info-box">
                            <strong>ℹ️ Note:</strong> Empty time slots will be ignored. Only filled time slots will trigger automatic processing.
                        </div>
                    </div>
                    
                    <!-- Weekly Schedule Configuration -->
                    <div class="form-section">
                        <div class="form-section-title">
                            📅 Weekly Schedule Configuration
                        </div>
                        <div class="form-section-description">
                            Select which days of the week the system should process orders. If a day is unchecked, the system will not process orders on that day, even if time slots are configured.
                        </div>
                        
                        <div class="weekly-schedule">
                            <div class="day-checkbox">
                                <input 
                                    type="checkbox" 
                                    id="monday" 
                                    name="monday" 
                                    <?php echo $weekly_schedule['monday'] ? 'checked' : ''; ?>
                                >
                                <label for="monday">Monday</label>
                            </div>
                            
                            <div class="day-checkbox">
                                <input 
                                    type="checkbox" 
                                    id="tuesday" 
                                    name="tuesday" 
                                    <?php echo $weekly_schedule['tuesday'] ? 'checked' : ''; ?>
                                >
                                <label for="tuesday">Tuesday</label>
                            </div>
                            
                            <div class="day-checkbox">
                                <input 
                                    type="checkbox" 
                                    id="wednesday" 
                                    name="wednesday" 
                                    <?php echo $weekly_schedule['wednesday'] ? 'checked' : ''; ?>
                                >
                                <label for="wednesday">Wednesday</label>
                            </div>
                            
                            <div class="day-checkbox">
                                <input 
                                    type="checkbox" 
                                    id="thursday" 
                                    name="thursday" 
                                    <?php echo $weekly_schedule['thursday'] ? 'checked' : ''; ?>
                                >
                                <label for="thursday">Thursday</label>
                            </div>
                            
                            <div class="day-checkbox">
                                <input 
                                    type="checkbox" 
                                    id="friday" 
                                    name="friday" 
                                    <?php echo $weekly_schedule['friday'] ? 'checked' : ''; ?>
                                >
                                <label for="friday">Friday</label>
                            </div>
                            
                            <div class="day-checkbox">
                                <input 
                                    type="checkbox" 
                                    id="saturday" 
                                    name="saturday" 
                                    <?php echo $weekly_schedule['saturday'] ? 'checked' : ''; ?>
                                >
                                <label for="saturday">Saturday</label>
                            </div>
                            
                            <div class="day-checkbox">
                                <input 
                                    type="checkbox" 
                                    id="sunday" 
                                    name="sunday" 
                                    <?php echo $weekly_schedule['sunday'] ? 'checked' : ''; ?>
                                >
                                <label for="sunday">Sunday</label>
                            </div>
                        </div>
                        
                        <div class="info-box">
                            <strong>⚠️ Important:</strong> The system will ONLY process on checked days. Unchecked days will be skipped entirely, regardless of time slot configuration.
                        </div>
                    </div>
                    
                    <!-- Form Actions -->
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">
                            💾 Save Configuration
                        </button>
                        <button type="reset" class="btn btn-secondary">
                            ↺ Reset Form
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Monitor Control Card -->
        <div class="card">
            <div class="card-header">
                <h2>
                    <span class="icon">🚀</span>
                    Real-Time Monitor Control
                </h2>
                <p>Start or stop the real-time order processing monitor</p>
            </div>
            
            <div class="card-body">
                <div class="form-section">
                    <div class="form-section-description">
                        The real-time monitor checks for new orders every minute and processes them automatically. 
                        It also processes at scheduled times configured above (08:00, 15:01, etc.).
                    </div>
                    
                    <div class="monitor-control">
                        <div class="monitor-status" id="monitorStatus">
                            <div class="status-indicator" id="statusIndicator">
                                <span class="status-dot status-offline"></span>
                                <span class="status-text">Status: Unknown</span>
                            </div>
                        </div>
                        
                        <div class="monitor-actions">
                            <button type="button" class="btn btn-success" id="startMonitorBtn" onclick="startMonitor()">
                                ▶️ Start Monitor
                            </button>
                            <button type="button" class="btn btn-danger" id="stopMonitorBtn" onclick="stopMonitor()" style="display: none;">
                                ⏹️ Stop Monitor
                            </button>
                            <button type="button" class="btn btn-secondary" onclick="checkMonitorStatus()">
                                🔄 Refresh Status
                            </button>
                        </div>
                        
                        <div class="info-box" style="margin-top: 20px;">
                            <strong>ℹ️ Note:</strong> The monitor runs in the background. Use this button to start it remotely. 
                            To stop the monitor, click "Stop Monitor" or press Ctrl+C in the terminal where it's running.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        &copy; 2025 Bol.com Order Processing System | Admin Panel v1.0
    </div>
    
    <script>
        // Auto-dismiss success messages after 5 seconds
        setTimeout(function() {
            const successAlert = document.querySelector('.alert-success');
            if (successAlert) {
                successAlert.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => successAlert.remove(), 300);
            }
        }, 5000);
        
        // Add animation for slide out
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideOut {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(-10px);
                }
            }
        `;
        document.head.appendChild(style);
        
        // Monitor control functions
        function updateMonitorStatus(status) {
            const indicator = document.getElementById('statusIndicator');
            const statusText = indicator.querySelector('.status-text');
            const statusDot = indicator.querySelector('.status-dot');
            const startBtn = document.getElementById('startMonitorBtn');
            const stopBtn = document.getElementById('stopMonitorBtn');
            
            statusDot.className = 'status-dot';
            
            if (status === 'running') {
                statusDot.classList.add('status-online');
                statusText.textContent = 'Status: Running';
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-flex';
            } else if (status === 'stopped') {
                statusDot.classList.add('status-offline');
                statusText.textContent = 'Status: Stopped';
                startBtn.style.display = 'inline-flex';
                stopBtn.style.display = 'none';
            } else {
                statusDot.classList.add('status-unknown');
                statusText.textContent = 'Status: Unknown';
                startBtn.style.display = 'inline-flex';
                stopBtn.style.display = 'none';
            }
        }
        
        function startMonitor() {
            if (!confirm('Start the real-time monitor? This will begin processing orders every minute.')) {
                return;
            }
            
            const startBtn = document.getElementById('startMonitorBtn');
            startBtn.disabled = true;
            startBtn.textContent = '⏳ Starting...';
            
            fetch('start_monitor.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: 'start' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateMonitorStatus('running');
                    alert('✅ Monitor started successfully!');
                } else {
                    alert('❌ Error: ' + (data.message || 'Failed to start monitor'));
                    updateMonitorStatus('stopped');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('❌ Error starting monitor: ' + error.message);
                updateMonitorStatus('stopped');
            })
            .finally(() => {
                startBtn.disabled = false;
                startBtn.textContent = '▶️ Start Monitor';
            });
        }
        
        function stopMonitor() {
            if (!confirm('Stop the real-time monitor? This will stop processing orders.')) {
                return;
            }
            
            const stopBtn = document.getElementById('stopMonitorBtn');
            stopBtn.disabled = true;
            stopBtn.textContent = '⏳ Stopping...';
            
            fetch('start_monitor.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: 'stop' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateMonitorStatus('stopped');
                    alert('✅ Monitor stopped successfully!');
                } else {
                    alert('❌ Error: ' + (data.message || 'Failed to stop monitor'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('❌ Error stopping monitor: ' + error.message);
            })
            .finally(() => {
                stopBtn.disabled = false;
                stopBtn.textContent = '⏹️ Stop Monitor';
            });
        }
        
        function checkMonitorStatus() {
            const refreshBtn = event.target;
            refreshBtn.disabled = true;
            refreshBtn.textContent = '🔄 Checking...';
            
            fetch('start_monitor.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: 'status' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status) {
                    updateMonitorStatus(data.status);
                } else {
                    updateMonitorStatus('unknown');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                updateMonitorStatus('unknown');
            })
            .finally(() => {
                refreshBtn.disabled = false;
                refreshBtn.textContent = '🔄 Refresh Status';
            });
        }
        
        // Check status on page load
        window.addEventListener('load', function() {
            checkMonitorStatus();
        });
    </script>
</body>
</html>

