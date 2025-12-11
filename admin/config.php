<?php
/**
 * Configuration Helper
 * Reads and writes to the Python config file
 */

class ConfigManager {
    private $config_file;
    private $config;
    
    public function __construct() {
        // Path to the Python config file (relative to admin directory)
        $this->config_file = dirname(__DIR__) . '/admin_config.json';
        $this->load();
    }
    
    /**
     * Load configuration from JSON file
     */
    private function load() {
        if (file_exists($this->config_file)) {
            $json = file_get_contents($this->config_file);
            $this->config = json_decode($json, true);
            
            if ($this->config === null) {
                $this->config = $this->getDefaultConfig();
            }
        } else {
            $this->config = $this->getDefaultConfig();
            $this->save();
        }
    }
    
    /**
     * Get default configuration
     */
    private function getDefaultConfig() {
        return [
            'processing_times' => [
                '08:30',
                '15:01',
                '',
                ''
            ],
            'weekly_schedule' => [
                'monday' => true,
                'tuesday' => true,
                'wednesday' => true,
                'thursday' => true,
                'friday' => true,
                'saturday' => false,
                'sunday' => false
            ],
            'last_updated' => date('Y-m-d H:i:s')
        ];
    }
    
    /**
     * Save configuration to JSON file
     */
    public function save() {
        $json = json_encode($this->config, JSON_PRETTY_PRINT);
        return file_put_contents($this->config_file, $json) !== false;
    }
    
    /**
     * Get all configuration
     */
    public function getAll() {
        return $this->config;
    }
    
    /**
     * Get processing times
     */
    public function getProcessingTimes() {
        return $this->config['processing_times'] ?? ['08:30', '15:01', '', ''];
    }
    
    /**
     * Get weekly schedule
     */
    public function getWeeklySchedule() {
        return $this->config['weekly_schedule'] ?? [
            'monday' => true,
            'tuesday' => true,
            'wednesday' => true,
            'thursday' => true,
            'friday' => true,
            'saturday' => false,
            'sunday' => false
        ];
    }
    
    /**
     * Update processing times
     */
    public function updateProcessingTimes($times) {
        // Ensure we have exactly 4 time slots
        $times = array_slice(array_pad($times, 4, ''), 0, 4);
        
        // Validate time format (HH:MM or empty)
        foreach ($times as $i => $time) {
            if ($time !== '' && !preg_match('/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/', $time)) {
                throw new Exception("Invalid time format for slot " . ($i + 1));
            }
        }
        
        $this->config['processing_times'] = $times;
        $this->config['last_updated'] = date('Y-m-d H:i:s');
    }
    
    /**
     * Update weekly schedule
     */
    public function updateWeeklySchedule($schedule) {
        $days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
        
        $weekly_schedule = [];
        foreach ($days as $day) {
            $weekly_schedule[$day] = isset($schedule[$day]) && $schedule[$day] === 'on';
        }
        
        $this->config['weekly_schedule'] = $weekly_schedule;
        $this->config['last_updated'] = date('Y-m-d H:i:s');
    }
    
    /**
     * Get last updated timestamp
     */
    public function getLastUpdated() {
        return $this->config['last_updated'] ?? 'Never';
    }
}

