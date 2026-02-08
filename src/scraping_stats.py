"""
Scraping Statistics Tracker

Maintains a registry of scraping runs with detailed metrics:
- Platform-wise statistics
- Page-by-page breakdown  
- 3-tier filtering metrics
- Timing and efficiency data

Stores in both database and CSV for easy viewing
"""

import sqlite3
import csv
import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Database and CSV paths
DB_PATH = Path(__file__).parent.parent / 'data' / 'jobs.db'
CSV_PATH = Path(__file__).parent.parent / 'data' / 'scraping_stats.csv'


def init_scraping_stats_table():
    """Create scraping_stats table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraping_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT NOT NULL,
            platform TEXT NOT NULL,
            search_name TEXT,
            search_url TEXT,
            pages_scraped INTEGER DEFAULT 0,
            total_cards_seen INTEGER DEFAULT 0,
            tier1_filtered INTEGER DEFAULT 0,
            tier2_skipped INTEGER DEFAULT 0,
            tier3_filtered INTEGER DEFAULT 0,
            jobs_collected INTEGER DEFAULT 0,
            efficiency_percent REAL DEFAULT 0,
            duration_seconds REAL DEFAULT 0,
            page_details TEXT,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Scraping stats table initialized")


def log_scraping_run(platform, search_name, stats_data):
    """
    Log a scraping run to database and CSV
    
    Args:
        platform: 'linkedin', 'seek', or 'jora'
        search_name: Name/description of the search
        stats_data: Dictionary with scraping statistics
            {
                'search_url': str,
                'pages_scraped': int,
                'total_cards_seen': int,
                'tier1_filtered': int,
                'tier2_skipped': int,
                'tier3_filtered': int,
                'jobs_collected': int,
                'efficiency_percent': float,
                'duration_seconds': float,
                'page_details': list[dict],  # Optional page-by-page stats
                'error_message': str  # Optional error
            }
    """
    try:
        init_scraping_stats_table()
        
        run_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate efficiency if not provided
        total_cards = stats_data.get('total_cards_seen', 0)
        total_filtered = (
            stats_data.get('tier1_filtered', 0) + 
            stats_data.get('tier2_skipped', 0) + 
            stats_data.get('tier3_filtered', 0)
        )
        efficiency = (total_filtered / total_cards * 100) if total_cards > 0 else 0
        
        # Prepare data
        page_details_json = json.dumps(stats_data.get('page_details', []))
        
        # Insert into database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scraping_runs (
                run_timestamp, platform, search_name, search_url,
                pages_scraped, total_cards_seen,
                tier1_filtered, tier2_skipped, tier3_filtered,
                jobs_collected, efficiency_percent, duration_seconds,
                page_details, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_timestamp,
            platform,
            search_name,
            stats_data.get('search_url', ''),
            stats_data.get('pages_scraped', 0),
            total_cards,
            stats_data.get('tier1_filtered', 0),
            stats_data.get('tier2_skipped', 0),
            stats_data.get('tier3_filtered', 0),
            stats_data.get('jobs_collected', 0),
            stats_data.get('efficiency_percent', efficiency),
            stats_data.get('duration_seconds', 0),
            page_details_json,
            stats_data.get('error_message', '')
        ))
        
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Append to CSV
        _append_to_csv(run_timestamp, platform, search_name, stats_data, efficiency)
        
        logger.info(f"Logged scraping run #{run_id} for {platform}: {search_name}")
        return run_id
        
    except Exception as e:
        logger.error(f"Failed to log scraping run: {e}")
        return None


def _append_to_csv(run_timestamp, platform, search_name, stats_data, efficiency):
    """Append scraping stats to CSV file"""
    try:
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists to write header
        file_exists = CSV_PATH.exists()
        
        with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    'Timestamp',
                    'Platform',
                    'Search Name',
                    'Pages Scraped',
                    'Total Cards',
                    'Tier 1 Filtered',
                    'Tier 2 Skipped',
                    'Tier 3 Filtered',
                    'Jobs Collected',
                    'Efficiency %',
                    'Duration (sec)',
                    'Error'
                ])
            
            # Write data row
            writer.writerow([
                run_timestamp,
                platform,
                search_name,
                stats_data.get('pages_scraped', 0),
                stats_data.get('total_cards_seen', 0),
                stats_data.get('tier1_filtered', 0),
                stats_data.get('tier2_skipped', 0),
                stats_data.get('tier3_filtered', 0),
                stats_data.get('jobs_collected', 0),
                f"{efficiency:.1f}",
                f"{stats_data.get('duration_seconds', 0):.1f}",
                stats_data.get('error_message', '')
            ])
            
    except Exception as e:
        logger.error(f"Failed to append to CSV: {e}")


def get_recent_runs(platform=None, days=7, limit=100):
    """
    Get recent scraping runs
    
    Args:
        platform: Filter by platform ('linkedin', 'seek', 'jora') or None for all
        days: Number of days to look back
        limit: Maximum number of runs to return
    
    Returns:
        List of dictionaries with run data
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM scraping_runs
            WHERE datetime(run_timestamp) >= datetime('now', '-{} days')
        '''.format(days)
        
        if platform:
            query += " AND platform = ?"
            cursor.execute(query + " ORDER BY run_timestamp DESC LIMIT ?", (platform, limit))
        else:
            cursor.execute(query + " ORDER BY run_timestamp DESC LIMIT ?", (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"Failed to get recent runs: {e}")
        return []


def get_daily_summary(date=None):
    """
    Get summary statistics for a specific date
    
    Args:
        date: Date string 'YYYY-MM-DD' or None for today
    
    Returns:
        Dictionary with aggregated stats per platform
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                platform,
                COUNT(*) as searches_run,
                SUM(pages_scraped) as total_pages,
                SUM(total_cards_seen) as total_cards,
                SUM(tier1_filtered) as total_tier1,
                SUM(tier2_skipped) as total_tier2,
                SUM(tier3_filtered) as total_tier3,
                SUM(jobs_collected) as total_jobs,
                AVG(efficiency_percent) as avg_efficiency,
                SUM(duration_seconds) as total_duration
            FROM scraping_runs
            WHERE DATE(run_timestamp) = ?
            GROUP BY platform
        ''', (date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        summary = {}
        for row in rows:
            platform = row[0]
            summary[platform] = {
                'searches_run': row[1],
                'total_pages': row[2],
                'total_cards_seen': row[3],
                'tier1_filtered': row[4],
                'tier2_skipped': row[5],
                'tier3_filtered': row[6],
                'jobs_collected': row[7],
                'avg_efficiency': row[8],
                'total_duration': row[9]
            }
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get daily summary: {e}")
        return {}


def export_stats_to_excel(output_path=None, days=30):
    """
    Export scraping statistics to Excel-compatible CSV
    
    Args:
        output_path: Path to save CSV (default: data/scraping_stats_export.csv)
        days: Number of days of history to export
    """
    if output_path is None:
        output_path = Path(__file__).parent.parent / 'data' / 'scraping_stats_export.csv'
    
    try:
        runs = get_recent_runs(days=days, limit=10000)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'run_timestamp', 'platform', 'search_name',
                'pages_scraped', 'total_cards_seen',
                'tier1_filtered', 'tier2_skipped', 'tier3_filtered',
                'jobs_collected', 'efficiency_percent', 'duration_seconds',
                'error_message'
            ])
            
            writer.writeheader()
            for run in runs:
                # Remove page_details (too verbose for Excel)
                run_copy = run.copy()
                run_copy.pop('page_details', None)
                run_copy.pop('created_at', None)
                run_copy.pop('search_url', None)
                writer.writerow(run_copy)
        
        logger.info(f"Exported {len(runs)} runs to {output_path}")
        print(f"✅ Exported {len(runs)} scraping runs to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to export to Excel: {e}")
        return None


if __name__ == '__main__':
    # Test/demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n📊 SCRAPING STATISTICS TRACKER")
    print("=" * 70)
    
    # Initialize
    init_scraping_stats_table()
    
    # Show recent runs
    runs = get_recent_runs(days=7, limit=10)
    print(f"\n📋 Recent Runs (last 7 days): {len(runs)}")
    for run in runs[:5]:
        print(f"  • {run['run_timestamp']} - {run['platform'].upper()}: {run['search_name']}")
        print(f"    Pages: {run['pages_scraped']}, Jobs: {run['jobs_collected']}, Efficiency: {run['efficiency_percent']:.1f}%")
    
    # Show today's summary
    summary = get_daily_summary()
    if summary:
        print(f"\n📈 Today's Summary:")
        for platform, stats in summary.items():
            print(f"\n  {platform.upper()}:")
            print(f"    Searches: {stats['searches_run']}")
            print(f"    Pages: {stats['total_pages']}")
            print(f"    Jobs: {stats['jobs_collected']}")
            print(f"    Efficiency: {stats['avg_efficiency']:.1f}%")
    
    # Export option
    print(f"\n💾 CSV Stats File: {CSV_PATH}")
    print(f"   (Open in Excel for easy viewing)")
