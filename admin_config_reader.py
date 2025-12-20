"""
Admin Configuration Reader
Reads configuration from the admin panel and integrates with the Python scheduler
"""

import json
import os
from typing import Dict, List, Tuple
from datetime import datetime

class AdminConfigReader:
    """Read and parse admin panel configuration"""
    
    def __init__(self, config_file: str = "admin_config.json"):
        """
        Initialize the config reader
        
        Args:
            config_file: Path to the admin config JSON file
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading admin config: {e}")
                return self._get_default_config()
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'processing_times': ['08:30', '15:01', '', ''],
            'weekly_schedule': {
                'monday': True,
                'tuesday': True,
                'wednesday': True,
                'thursday': True,
                'friday': True,
                'saturday': False,
                'sunday': False
            },
            'last_updated': None
        }
    
    def get_processing_times(self) -> List[str]:
        """
        Get list of processing times (non-empty only)
        
        Returns:
            List of time strings in HH:MM format
        """
        times = self.config.get('processing_times', [])
        # Filter out empty strings
        return [t for t in times if t and t.strip()]
    
    def get_weekly_schedule(self) -> Dict[str, bool]:
        """
        Get weekly schedule configuration
        
        Returns:
            Dictionary mapping day names to boolean (enabled/disabled)
        """
        return self.config.get('weekly_schedule', {
            'monday': True,
            'tuesday': True,
            'wednesday': True,
            'thursday': True,
            'friday': True,
            'saturday': False,
            'sunday': False
        })
    
    def is_processing_enabled_today(self) -> bool:
        """
        Check if processing is enabled for today
        
        Returns:
            True if today is enabled, False otherwise
        """
        today = datetime.now().strftime('%A').lower()
        schedule = self.get_weekly_schedule()
        return schedule.get(today, True)
    
    def is_processing_enabled_for_day(self, day: str) -> bool:
        """
        Check if processing is enabled for a specific day
        
        Args:
            day: Day name (e.g., 'monday', 'tuesday')
            
        Returns:
            True if enabled, False otherwise
        """
        schedule = self.get_weekly_schedule()
        return schedule.get(day.lower(), True)
    
    def should_process_now(self) -> bool:
        """
        Check if processing should happen now based on configuration
        
        Returns:
            True if processing should happen, False otherwise
        """
        # Check if today is enabled
        if not self.is_processing_enabled_today():
            return False
        
        # Get current time
        current_time = datetime.now().strftime('%H:%M')
        processing_times = self.get_processing_times()
        
        # Check if current time matches any processing time
        return current_time in processing_times
    
    def get_next_processing_time(self) -> Tuple[str, str]:
        """
        Get the next scheduled processing time
        
        Returns:
            Tuple of (day_name, time_string) or (None, None) if none configured
        """
        times = self.get_processing_times()
        if not times:
            return (None, None)
        
        current_day = datetime.now().strftime('%A').lower()
        current_time = datetime.now().strftime('%H:%M')
        schedule = self.get_weekly_schedule()
        
        # Check remaining times today
        if schedule.get(current_day, False):
            for time in times:
                if time > current_time:
                    return (current_day.capitalize(), time)
        
        # Check next days
        days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_day_index = days_order.index(current_day)
        
        for i in range(1, 8):  # Check next 7 days
            next_day_index = (current_day_index + i) % 7
            next_day = days_order[next_day_index]
            
            if schedule.get(next_day, False):
                if times:
                    return (next_day.capitalize(), times[0])
        
        return (None, None)
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()


# Example usage
if __name__ == "__main__":
    reader = AdminConfigReader()
    
    print("="*80)
    print("ADMIN CONFIGURATION")
    print("="*80)
    
    print("\n⏰ Processing Times:")
    times = reader.get_processing_times()
    if times:
        for i, time in enumerate(times, 1):
            print(f"  {i}. {time}")
    else:
        print("  No processing times configured")
    
    print("\n📅 Weekly Schedule:")
    schedule = reader.get_weekly_schedule()
    for day, enabled in schedule.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"  {day.capitalize():12s} {status}")
    
    print(f"\n🔍 Processing enabled today: {'Yes ✅' if reader.is_processing_enabled_today() else 'No ❌'}")
    
    next_day, next_time = reader.get_next_processing_time()
    if next_day and next_time:
        print(f"⏰ Next processing: {next_day} at {next_time}")
    else:
        print("⏰ No processing times configured")
    
    print("="*80)

