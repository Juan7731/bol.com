<?php
/**
 * Start/Stop Monitor API Endpoint
 * Handles starting and stopping the real-time monitor
 */

require_once 'auth.php';

header('Content-Type: application/json');

// Get the action from POST data
$input = json_decode(file_get_contents('php://input'), true);
$action = $input['action'] ?? $_POST['action'] ?? 'status';

// Get the project root directory (parent of admin directory)
$project_root = dirname(__DIR__);
$script_path = $project_root . DIRECTORY_SEPARATOR . 'run_realtime_monitor.py';
$bat_path = $project_root . DIRECTORY_SEPARATOR . 'run_realtime_monitor.bat';
$pid_file = $project_root . DIRECTORY_SEPARATOR . 'monitor.pid';
$log_file = $project_root . DIRECTORY_SEPARATOR . 'monitor.log';

function isWindows() {
    return strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
}

function getMonitorStatus() {
    global $pid_file, $script_path;
    
    if (!file_exists($pid_file)) {
        // Also check if process is running by script name (in case PID file is missing)
        if (isWindows()) {
            $output = [];
            exec('wmic process where "name=\'python.exe\'" get ProcessId,CommandLine /format:csv 2>NUL', $output);
            foreach ($output as $line) {
                if (stripos($line, basename($script_path)) !== false) {
                    // Found running process, extract PID and save it
                    $parts = str_getcsv($line);
                    if (isset($parts[1]) && is_numeric($parts[1])) {
                        file_put_contents($pid_file, $parts[1]);
                        return 'running';
                    }
                }
            }
        }
        return 'stopped';
    }
    
    $pid = trim(file_get_contents($pid_file));
    if (empty($pid) || !is_numeric($pid)) {
        return 'stopped';
    }
    
    if (isWindows()) {
        // Check if process is running on Windows
        $output = [];
        exec("tasklist /FI \"PID eq $pid\" /FO CSV 2>NUL", $output);
        $running = false;
        foreach ($output as $line) {
            if (stripos($line, 'python') !== false || stripos($line, 'python.exe') !== false) {
                $running = true;
                break;
            }
        }
        
        // If not found by PID, check by script name
        if (!$running) {
            $wmic_output = [];
            exec('wmic process where "name=\'python.exe\'" get ProcessId,CommandLine /format:csv 2>NUL', $wmic_output);
            foreach ($wmic_output as $wmic_line) {
                if (stripos($wmic_line, basename($script_path)) !== false) {
                    $parts = str_getcsv($wmic_line);
                    if (isset($parts[1]) && $parts[1] == $pid) {
                        $running = true;
                        break;
                    }
                }
            }
        }
        
        return $running ? 'running' : 'stopped';
    } else {
        // Check if process is running on Linux/Unix
        $result = exec("ps -p $pid -o pid= 2>/dev/null");
        return !empty($result) ? 'running' : 'stopped';
    }
}

function startMonitor() {
    global $project_root, $script_path, $bat_path, $pid_file, $log_file;
    
    // Check if already running
    $status = getMonitorStatus();
    if ($status === 'running') {
        return ['success' => false, 'message' => 'Monitor is already running'];
    }
    
    // Verify script exists
    if (!file_exists($script_path)) {
        return ['success' => false, 'message' => 'Monitor script not found: ' . basename($script_path)];
    }
    
    // Change to project directory
    $old_dir = getcwd();
    chdir($project_root);
    
    try {
        if (isWindows()) {
            // Method 1: Try using the batch file helper
            $batch_helper = $project_root . DIRECTORY_SEPARATOR . 'start_monitor_background.bat';
            if (file_exists($batch_helper)) {
                $command = sprintf('"%s"', $batch_helper);
                exec($command, $batch_output, $batch_return);
                sleep(2);
                
                if (file_exists($pid_file)) {
                    $pid = trim(file_get_contents($pid_file));
                    if (!empty($pid) && is_numeric($pid)) {
                        $status = getMonitorStatus();
                        if ($status === 'running') {
                            return ['success' => true, 'message' => 'Monitor started successfully (PID: ' . $pid . ')', 'pid' => $pid];
                        }
                    }
                }
            }
            
            // Method 2: Use PowerShell
            $ps_script = $project_root . DIRECTORY_SEPARATOR . 'start_monitor.ps1';
            $ps_content = sprintf(
                '$process = Start-Process -FilePath "python" -ArgumentList "%s" -PassThru -WindowStyle Hidden -RedirectStandardOutput "%s" -RedirectStandardError "%s"' . "\n" .
                'if ($process) {' . "\n" .
                '    $process.Id | Out-File -FilePath "%s" -Encoding ASCII' . "\n" .
                '    Write-Output $process.Id' . "\n" .
                '} else {' . "\n" .
                '    Write-Output "ERROR"' . "\n" .
                '}',
                str_replace('"', '\"', $script_path),
                str_replace('\\', '/', $log_file),
                str_replace('\\', '/', $log_file),
                str_replace('\\', '/', $pid_file)
            );
            
            file_put_contents($ps_script, $ps_content);
            
            $command = sprintf(
                'powershell.exe -ExecutionPolicy Bypass -File "%s"',
                $ps_script
            );
            
            $output = [];
            $return_var = 0;
            exec($command . ' 2>&1', $output, $return_var);
            
            $pid = trim(implode('', $output));
            sleep(2);
            
            if (!empty($pid) && is_numeric($pid) && $pid !== 'ERROR') {
                $status = getMonitorStatus();
                if ($status === 'running') {
                    return ['success' => true, 'message' => 'Monitor started successfully (PID: ' . $pid . ')', 'pid' => $pid];
                }
            }
            
            // Method 3: Simple start command and find process
            $alt_command = sprintf(
                'start /B "" python "%s"',
                $script_path
            );
            
            exec($alt_command, $alt_output, $alt_return);
            sleep(3);
            
            // Find process by script name
            $wmic_output = [];
            exec('wmic process where "name=\'python.exe\'" get ProcessId,CommandLine /format:csv 2>NUL', $wmic_output);
            
            foreach ($wmic_output as $wmic_line) {
                if (stripos($wmic_line, basename($script_path)) !== false) {
                    $parts = str_getcsv($wmic_line);
                    if (isset($parts[1]) && is_numeric($parts[1])) {
                        file_put_contents($pid_file, $parts[1]);
                        $pid = $parts[1];
                        $status = getMonitorStatus();
                        if ($status === 'running') {
                            return ['success' => true, 'message' => 'Monitor started successfully (PID: ' . $pid . ')', 'pid' => $pid];
                        }
                    }
                }
            }
            
            // If we get here, all methods failed
            $error_details = [];
            if (file_exists($log_file)) {
                $log_content = file_get_contents($log_file);
                if (!empty($log_content)) {
                    $error_details[] = 'Last log: ' . substr($log_content, -200);
                }
            }
            
            // Check if Python is available
            $python_check = [];
            exec('python --version 2>&1', $python_check);
            if (empty($python_check)) {
                $error_details[] = 'Python may not be installed or not in PATH';
            }
            
            $error_msg = 'Failed to start monitor. ';
            if (!empty($error_details)) {
                $error_msg .= implode(' | ', $error_details);
            } else {
                $error_msg .= 'Please check: 1) Python is installed, 2) Script exists, 3) Check ' . basename($log_file) . ' for errors';
            }
            
            return ['success' => false, 'message' => $error_msg];
        } else {
            // Linux/Unix: Start in background
            $command = sprintf(
                'nohup python3 "%s" > "%s" 2>&1 & echo $!',
                $script_path,
                $log_file
            );
            
            $pid = trim(exec($command));
            
            if (!empty($pid) && is_numeric($pid)) {
                file_put_contents($pid_file, $pid);
                return ['success' => true, 'message' => 'Monitor started successfully', 'pid' => $pid];
            } else {
                return ['success' => false, 'message' => 'Failed to start monitor process'];
            }
        }
    } catch (Exception $e) {
        return ['success' => false, 'message' => 'Error: ' . $e->getMessage()];
    } finally {
        chdir($old_dir);
    }
}

function stopMonitor() {
    global $pid_file;
    
    $status = getMonitorStatus();
    if ($status === 'stopped') {
        return ['success' => false, 'message' => 'Monitor is not running'];
    }
    
    if (!file_exists($pid_file)) {
        return ['success' => false, 'message' => 'PID file not found'];
    }
    
    $pid = trim(file_get_contents($pid_file));
    if (empty($pid)) {
        return ['success' => false, 'message' => 'Invalid PID'];
    }
    
    try {
        if (isWindows()) {
            // Windows: Kill process
            exec("taskkill /PID $pid /F 2>NUL", $output, $return_var);
        } else {
            // Linux/Unix: Kill process
            exec("kill $pid 2>/dev/null", $output, $return_var);
        }
        
        // Wait a moment
        sleep(1);
        
        // Check if stopped
        $status = getMonitorStatus();
        if ($status === 'stopped') {
            // Remove PID file
            if (file_exists($pid_file)) {
                unlink($pid_file);
            }
            return ['success' => true, 'message' => 'Monitor stopped successfully'];
        } else {
            return ['success' => false, 'message' => 'Failed to stop monitor'];
        }
    } catch (Exception $e) {
        return ['success' => false, 'message' => 'Error: ' . $e->getMessage()];
    }
}

// Handle the action
switch ($action) {
    case 'start':
        $result = startMonitor();
        echo json_encode($result);
        break;
        
    case 'stop':
        $result = stopMonitor();
        echo json_encode($result);
        break;
        
    case 'status':
    default:
        $status = getMonitorStatus();
        echo json_encode(['success' => true, 'status' => $status]);
        break;
}
?>


