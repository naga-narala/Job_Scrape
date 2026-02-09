#!/usr/bin/env python3
"""
View Scraping Statistics

Quick script to view scraping run statistics from database and CSV
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraping_stats import (
    get_recent_runs,
    get_daily_summary,
    export_stats_to_excel,
    init_scraping_stats_table
)
from datetime import datetime, timedelta

def main():
    print("\n" + "="*80)
    print("📊 SCRAPING STATISTICS DASHBOARD")
    print("="*80)
    
    # Initialize table
    init_scraping_stats_table()
    
    # Get recent runs (last 7 days)
    runs = get_recent_runs(days=7, limit=50)
    
    if not runs:
        print("\n⚠️  No scraping runs found in the last 7 days")
        print("   Run the scraper with: python src/main.py")
        return
    
    # Group by date
    runs_by_date = {}
    for run in runs:
        date = run['run_timestamp'].split()[0]  # Extract date
        if date not in runs_by_date:
            runs_by_date[date] = []
        runs_by_date[date].append(run)
    
    # Display runs grouped by date
    for date in sorted(runs_by_date.keys(), reverse=True):
        day_runs = runs_by_date[date]
        print(f"\n📅 {date} ({len(day_runs)} runs)")
        print("-" * 80)
        
        for run in day_runs:
            platform_emoji = {
                'linkedin': '📘',
                'seek': '🟣',
                'jora': '🔵'
            }.get(run['platform'], '📋')
            
            print(f"{platform_emoji} {run['platform'].upper()}: {run['search_name']}")
            print(f"   Time: {run['run_timestamp'].split()[1]}")
            print(f"   Pages: {run['pages_scraped']} | Cards: {run['total_cards_seen']} | Jobs: {run['jobs_collected']}")
            print(f"   Tier 1: {run['tier1_filtered']} | Tier 2: {run['tier2_skipped']} | Tier 3: {run['tier3_filtered']}")
            print(f"   Efficiency: {run['efficiency_percent']:.1f}% | Duration: {run['duration_seconds']:.1f}s")
            if run['error_message']:
                print(f"   ❌ Error: {run['error_message']}")
            print()
    
    # Show daily summaries
    print("\n" + "="*80)
    print("📈 DAILY SUMMARIES")
    print("="*80)
    
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        summary = get_daily_summary(date)
        
        if summary:
            print(f"\n📅 {date}")
            print("-" * 80)
            
            total_jobs = sum(s['jobs_collected'] for s in summary.values())
            total_pages = sum(s['total_pages'] for s in summary.values())
            
            print(f"📊 TOTAL: {total_jobs} jobs from {total_pages} pages")
            
            for platform, stats in summary.items():
                platform_emoji = {
                    'linkedin': '📘',
                    'seek': '🟣',
                    'jora': '🔵'
                }.get(platform, '📋')
                
                print(f"\n{platform_emoji} {platform.upper()}:")
                print(f"   Searches: {stats['searches_run']}")
                print(f"   Pages: {stats['total_pages']}")
                print(f"   Cards: {stats['total_cards_seen']}")
                print(f"   Jobs: {stats['jobs_collected']}")
                print(f"   Filtered: T1={stats['tier1_filtered']} | T2={stats['tier2_skipped']} | T3={stats['tier3_filtered']}")
                print(f"   Avg Efficiency: {stats['avg_efficiency']:.1f}%")
                print(f"   Total Time: {stats['total_duration']:.0f}s ({stats['total_duration']/60:.1f} min)")
    
    # Export option
    print("\n" + "="*80)
    print("💾 EXPORT OPTIONS")
    print("="*80)
    print("\n1. CSV file: data/scraping_stats.csv (auto-appended on each run)")
    print("2. Excel export: Run export_stats_to_excel(days=30)")
    print("\n📊 To export last 30 days to Excel:")
    print("   python -c 'import sys; sys.path.insert(0, \"src\"); from scraping_stats import export_stats_to_excel; export_stats_to_excel(days=30)'")
    print()

if __name__ == '__main__':
    main()
