#!/usr/bin/env python3
"""
Monitor the running workflow test
"""

import time
import os

log_file = '/tmp/workflow_10pages_full.log'

print("=" * 80)
print("📊 WORKFLOW MONITOR - Live Progress")
print("=" * 80)
print(f"\nMonitoring: {log_file}")
print("Press Ctrl+C to stop monitoring (workflow will continue running)\n")

# Wait for log file to be created
while not os.path.exists(log_file):
    print("Waiting for log file to be created...")
    time.sleep(2)

# Track what we've already printed
last_position = 0

try:
    while True:
        with open(log_file, 'r') as f:
            # Seek to last position
            f.seek(last_position)
            
            # Read new content
            new_content = f.read()
            
            if new_content:
                # Extract key metrics
                for line in new_content.split('\n'):
                    if any(keyword in line for keyword in [
                        'Page ', 'Extracted:', 'Total cards', 'Tier 1', 
                        'Efficiency gain', 'Total extracted', 'PHASE',
                        'SCRAPING RESULTS', 'Jobs scraped:', 'Passed:', 
                        'Filtered:', 'New jobs:', 'Duplicates:'
                    ]):
                        # Clean up the line
                        clean_line = line.split(' - INFO - ')[-1] if ' - INFO - ' in line else line
                        clean_line = line.split(' - ERROR - ')[-1] if ' - ERROR - ' in line else clean_line
                        print(clean_line)
            
            # Update position
            last_position = f.tell()
        
        time.sleep(2)

except KeyboardInterrupt:
    print("\n\n" + "=" * 80)
    print("✅ Monitoring stopped (workflow still running in background)")
    print("=" * 80)
    print(f"\nTo continue monitoring: tail -f {log_file}")
    print(f"To see full log: cat {log_file}")
    print(f"To check if still running: ps aux | grep run_complete_workflow")
