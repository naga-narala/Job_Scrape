import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz

DB_PATH = Path(__file__).parent.parent / 'data' / 'jobs.db'


def get_perth_now():
    """Get current datetime in Perth timezone"""
    perth_tz = pytz.timezone('Australia/Perth')
    return datetime.now(perth_tz)


def get_perth_date():
    """Get current date in Perth timezone"""
    return get_perth_now().date()


def generate_job_hash(title, company, url):
    """Generate unique hash for job deduplication"""
    content = f"{title}|{company}|{url}".lower()
    return hashlib.sha256(content.encode()).hexdigest()


def get_profile_hash():
    """Generate MD5 hash of current profile.txt"""
    profile_path = Path(__file__).parent.parent / 'profile.txt'
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return hashlib.md5(content.encode()).hexdigest()
    except FileNotFoundError:
        return None


def get_connection():
    """Get database connection"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Create all database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id_hash TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            description TEXT,
            requirement_text TEXT,
            url TEXT NOT NULL,
            posted_date TEXT,
            employment_type TEXT,
            source_search_id TEXT,
            source TEXT DEFAULT 'linkedin',
            region TEXT DEFAULT 'australia',
            first_seen_date DATE NOT NULL,
            last_seen_date DATE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            applied BOOLEAN DEFAULT 0,
            rejected BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'new',
            applied_date DATE,
            rejected_date DATE,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Scores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            reasoning TEXT,
            matched TEXT,
            not_matched TEXT,
            key_points TEXT,
            model_used TEXT,
            profile_hash TEXT,
            scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    ''')
    
    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            notification_type TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    ''')
    
    # Profile changes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_hash TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rescore_triggered BOOLEAN DEFAULT 0
        )
    ''')
    
    # Rejections table (Phase 5)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rejections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            rejection_category TEXT NOT NULL,
            rejection_notes TEXT,
            rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(job_id_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_search ON jobs(source_search_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_dates ON jobs(first_seen_date, is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_scores_job ON scores(job_id)')
    
    conn.commit()
    conn.close()


def insert_job(job_data):
    """
    Insert new job into database
    Returns job_id if inserted, None if duplicate
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    job_hash = generate_job_hash(
        job_data['title'],
        job_data.get('company', ''),
        job_data['url']
    )
    
    # Check if already exists
    cursor.execute('SELECT id FROM jobs WHERE job_id_hash = ?', (job_hash,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return None
    
    # Insert new job
    today = get_perth_date()
    cursor.execute('''
        INSERT INTO jobs (
            job_id_hash, title, company, location, description, url,
            posted_date, employment_type, source_search_id, source, region,
            first_seen_date, last_seen_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_hash,
        job_data['title'],
        job_data.get('company'),
        job_data.get('location'),
        job_data.get('description'),
        job_data['url'],
        job_data.get('posted_date'),
        job_data.get('employment_type'),
        job_data.get('source_search_id'),
        job_data.get('source', 'linkedin'),
        job_data.get('region', 'australia'),
        today,
        today
    ))
    
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id


def update_job_last_seen(job_id_hash):
    """Update last_seen_date for existing job"""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = get_perth_date()
    cursor.execute('''
        UPDATE jobs 
        SET last_seen_date = ?, is_active = 1
        WHERE job_id_hash = ?
    ''', (today, job_id_hash))
    
    conn.commit()
    conn.close()


def mark_jobs_inactive(source_search_id, active_job_hashes):
    """Mark jobs as inactive if not seen in recent fetch"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if active_job_hashes:
        placeholders = ','.join('?' * len(active_job_hashes))
        cursor.execute(f'''
            UPDATE jobs
            SET is_active = 0
            WHERE source_search_id = ?
            AND job_id_hash NOT IN ({placeholders})
        ''', [source_search_id] + active_job_hashes)
    else:
        cursor.execute('''
            UPDATE jobs
            SET is_active = 0
            WHERE source_search_id = ?
        ''', (source_search_id,))
    
    conn.commit()
    conn.close()


def get_unscored_jobs():
    """Get all jobs without a score"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.* FROM jobs j
        LEFT JOIN scores s ON j.id = s.job_id
        WHERE s.id IS NULL
        ORDER BY j.first_seen_date DESC
    ''')
    
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs


def insert_score(job_id, score_data, profile_hash):
    """Insert score for a job"""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    
    # Convert lists to JSON strings for storage
    matched_json = json.dumps(score_data.get('matched', []))
    not_matched_json = json.dumps(score_data.get('not_matched', []))
    key_points_json = json.dumps(score_data.get('key_points', []))
    
    # Keep reasoning for backward compatibility
    reasoning = score_data.get('reasoning', '')
    if not reasoning and score_data.get('key_points'):
        reasoning = ' '.join(score_data['key_points'])
    
    cursor.execute('''
        INSERT INTO scores (job_id, score, reasoning, matched, not_matched, key_points, model_used, profile_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_id,
        score_data['score'],
        reasoning,
        matched_json,
        not_matched_json,
        key_points_json,
        score_data.get('model_used'),
        profile_hash
    ))
    
    conn.commit()
    conn.close()


def delete_score(job_id):
    """Delete score for a job (for rescoring)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM scores WHERE job_id = ?', (job_id,))
    
    conn.commit()
    conn.close()


def get_jobs_for_rescore(min_score, max_score, max_age_days, exclude_profile_hash):
    """Get jobs eligible for rescoring"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_date = get_perth_date() - timedelta(days=max_age_days)
    
    cursor.execute('''
        SELECT j.*, s.score as old_score
        FROM jobs j
        JOIN scores s ON j.id = s.job_id
        WHERE s.score >= ? AND s.score <= ?
        AND j.first_seen_date >= ?
        AND s.profile_hash != ?
        ORDER BY j.first_seen_date DESC
    ''', (min_score, max_score, cutoff_date, exclude_profile_hash))
    
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs


def get_high_scoring_unnotified(threshold):
    """Get jobs above threshold that haven't been notified"""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.*, s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used
        FROM jobs j
        JOIN scores s ON j.id = s.job_id
        LEFT JOIN notifications n ON j.id = n.job_id
        WHERE s.score >= ?
        AND n.id IS NULL
        ORDER BY s.score DESC, j.first_seen_date DESC
    ''', (threshold,))
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        # Parse JSON fields
        try:
            job['matched'] = json.loads(job.get('matched', '[]'))
        except:
            job['matched'] = []
        try:
            job['not_matched'] = json.loads(job.get('not_matched', '[]'))
        except:
            job['not_matched'] = []
        try:
            job['key_points'] = json.loads(job.get('key_points', '[]'))
        except:
            job['key_points'] = []
        jobs.append(job)
    
    conn.close()
    return jobs


def mark_notified(job_id, notification_type, status):
    """Mark job as notified"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO notifications (job_id, notification_type, status)
        VALUES (?, ?, ?)
    ''', (job_id, notification_type, status))
    
    conn.commit()
    conn.close()


def mark_applied(job_id):
    """Toggle applied status for a job"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT applied FROM jobs WHERE id = ?', (job_id,))
    row = cursor.fetchone()
    
    if row:
        new_status = 0 if row['applied'] else 1
        cursor.execute('UPDATE jobs SET applied = ? WHERE id = ?', (new_status, job_id))
        conn.commit()
    
    conn.close()


def get_job(job_id):
    """Get single job by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    job = cursor.fetchone()
    
    conn.close()
    return dict(job) if job else None


def get_jobs_by_date_range(days, hide_old_days=30):
    """Get jobs within date range, hiding jobs older than hide_old_days"""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    
    start_date = get_perth_date() - timedelta(days=days)
    hide_before = get_perth_date() - timedelta(days=hide_old_days)
    
    cursor.execute('''
        SELECT j.*, s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used
        FROM jobs j
        JOIN scores s ON j.id = s.job_id
        WHERE j.first_seen_date >= ?
        AND j.first_seen_date >= ?
        ORDER BY s.score DESC, j.first_seen_date DESC
    ''', (start_date, hide_before))
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        # Parse JSON fields
        try:
            job['matched'] = json.loads(job.get('matched', '[]'))
        except:
            job['matched'] = []
        try:
            job['not_matched'] = json.loads(job.get('not_matched', '[]'))
        except:
            job['not_matched'] = []
        try:
            job['key_points'] = json.loads(job.get('key_points', '[]'))
        except:
            job['key_points'] = []
        jobs.append(job)
    
    conn.close()
    return jobs


def get_all_jobs(include_inactive=False):
    """Get all jobs with scores"""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT j.*, s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used
        FROM jobs j
        JOIN scores s ON j.id = s.job_id
    '''
    
    if not include_inactive:
        query += ' WHERE j.is_active = 1'
    
    query += ' ORDER BY s.score DESC, j.first_seen_date DESC'
    
    cursor.execute(query)
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        # Parse JSON fields
        try:
            job['matched'] = json.loads(job.get('matched', '[]'))
        except:
            job['matched'] = []
        try:
            job['not_matched'] = json.loads(job.get('not_matched', '[]'))
        except:
            job['not_matched'] = []
        try:
            job['key_points'] = json.loads(job.get('key_points', '[]'))
        except:
            job['key_points'] = []
        jobs.append(job)
    
    conn.close()
    return jobs


def get_last_profile_hash():
    """Get the most recent profile hash"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT profile_hash FROM profile_changes
        ORDER BY changed_at DESC LIMIT 1
    ''')
    
    row = cursor.fetchone()
    conn.close()
    return row['profile_hash'] if row else None


def insert_profile_change(profile_hash):
    """Record profile change"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO profile_changes (profile_hash)
        VALUES (?)
    ''', (profile_hash,))
    
    conn.commit()
    conn.close()


def get_last_run_time():
    """Get timestamp of most recent job insertion"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT MAX(created_at) as last_run FROM jobs')
    row = cursor.fetchone()
    
    conn.close()
    return row['last_run'] if row and row['last_run'] else 'Never'


def count_all_jobs():
    """Count total jobs in database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM jobs')
    count = cursor.fetchone()['count']
    
    conn.close()
    return count


def count_jobs_above_threshold(threshold):
    """Count jobs scoring above threshold"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as count FROM jobs j
        JOIN scores s ON j.id = s.job_id
        WHERE s.score >= ?
    ''', (threshold,))
    
    count = cursor.fetchone()['count']
    conn.close()
    return count


def get_average_score():
    """Get average score of all scored jobs"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT AVG(score) as avg FROM scores')
    avg = cursor.fetchone()['avg']
    
    conn.close()
    return round(avg, 1) if avg else 0


def get_top_companies(limit=10):
    """Get top companies by job count"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT company, COUNT(*) as count
        FROM jobs
        WHERE company IS NOT NULL
        GROUP BY company
        ORDER BY count DESC
        LIMIT ?
    ''', (limit,))
    
    companies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return companies


def get_score_distribution():
    """Get distribution of scores"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN score >= 90 THEN 1 ELSE 0 END) as score_90_plus,
            SUM(CASE WHEN score >= 80 AND score < 90 THEN 1 ELSE 0 END) as score_80_89,
            SUM(CASE WHEN score >= 75 AND score < 80 THEN 1 ELSE 0 END) as score_75_79,
            SUM(CASE WHEN score < 75 THEN 1 ELSE 0 END) as score_below_75
        FROM scores
    ''')
    
    dist = dict(cursor.fetchone())
    conn.close()
    return dist


def mark_applied(job_id):
    """Mark job as applied"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE jobs
        SET applied = 1, status = 'applied', applied_date = ?
        WHERE id = ?
    ''', (get_perth_date(), job_id))
    
    conn.commit()
    conn.close()


def update_job_status(job_id, status, remarks=None):
    """Update job application status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE jobs
        SET status = ?, remarks = ?
        WHERE id = ?
    ''', (status, remarks, job_id))
    
    conn.commit()
    conn.close()


def get_job(job_id):
    """Get single job by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    job = cursor.fetchone()
    
    conn.close()
    return dict(job) if job else None


def get_applied_jobs():
    """Get all jobs where applied=1, ordered by applied_date"""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.*, s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used
        FROM jobs j
        LEFT JOIN scores s ON j.id = s.job_id
        WHERE j.applied = 1
        ORDER BY j.applied_date DESC, j.first_seen_date DESC
    ''')
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        # Parse JSON fields
        for field in ['matched', 'not_matched', 'key_points']:
            if job.get(field):
                try:
                    job[field] = json.loads(job[field])
                except:
                    pass
        jobs.append(job)
    
    conn.close()
    return jobs


def reject_job(job_id, rejection_category, rejection_notes=''):
    """
    Mark job as rejected and store rejection feedback
    
    Args:
        job_id: Job ID to reject
        rejection_category: Category of rejection (e.g., 'wrong_experience_level')
        rejection_notes: Additional notes about rejection
    
    Returns:
        True if successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Update job status
        today = get_perth_date()
        cursor.execute('''
            UPDATE jobs 
            SET rejected = 1, 
                rejected_date = ?,
                status = 'rejected'
            WHERE id = ?
        ''', (today, job_id))
        
        # Insert rejection record
        cursor.execute('''
            INSERT INTO rejections (job_id, rejection_category, rejection_notes)
            VALUES (?, ?, ?)
        ''', (job_id, rejection_category, rejection_notes))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error rejecting job: {e}")
        return False


def get_rejected_jobs():
    """Get all jobs where rejected=1, ordered by rejected_date"""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.*, s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used,
               r.rejection_category, r.rejection_notes, r.rejected_at
        FROM jobs j
        LEFT JOIN scores s ON j.id = s.job_id
        LEFT JOIN rejections r ON j.id = r.job_id
        WHERE j.rejected = 1
        ORDER BY j.rejected_date DESC, j.first_seen_date DESC
    ''')
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        # Parse JSON fields
        for field in ['matched', 'not_matched', 'key_points']:
            if job.get(field):
                try:
                    job[field] = json.loads(job[field])
                except:
                    pass
        jobs.append(job)
    
    conn.close()
    return jobs


def get_rejection_stats():
    """Get rejection statistics for dashboard analytics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            rejection_category,
            COUNT(*) as count
        FROM rejections
        GROUP BY rejection_category
        ORDER BY count DESC
    ''')
    
    stats = {}
    for row in cursor.fetchall():
        stats[row['rejection_category']] = row['count']
    
    conn.close()
    return stats
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        # Parse JSON fields
        if job.get('matched'):
            job['matched'] = json.loads(job['matched'])
        if job.get('not_matched'):
            job['not_matched'] = json.loads(job['not_matched'])
        if job.get('key_points'):
            job['key_points'] = json.loads(job['key_points'])
        jobs.append(job)
    
    conn.close()
    return jobs
