import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Load database path from config
config_path = Path(__file__).parent.parent / 'config.json'
with open(config_path, 'r') as f:
    _DB_CONFIG = json.load(f)

DB_PATH = Path(__file__).parent.parent / _DB_CONFIG.get('database', {}).get('path', 'data/jobs.db')


def get_perth_now():
    """Get current datetime in Perth timezone"""
    perth_tz = pytz.timezone('Australia/Perth')
    return datetime.now(perth_tz)


def get_perth_date():
    """Get current date in Perth timezone"""
    return get_perth_now().date()


def normalize_company_name(company):
    """
    Normalize company name for better deduplication
    
    Removes common suffixes and standardizes format:
    - "Company Pty Ltd" → "company"
    - "Company Inc." → "company"
    - "Company    Name" → "company name" (normalize whitespace)
    
    Args:
        company: Raw company name
    
    Returns:
        Normalized company name (lowercase, no suffixes, clean whitespace)
    """
    if not company:
        return ''
    
    # Convert to lowercase
    normalized = company.lower().strip()
    
    # Remove common company suffixes (Australian, US, UK formats)
    suffixes = [
        r'\s+pty\.?\s+ltd\.?$',  # Pty Ltd, Pty. Ltd.
        r'\s+pty$',               # Pty
        r'\s+ltd\.?$',           # Ltd, Ltd.
        r'\s+limited$',           # Limited
        r'\s+inc\.?$',           # Inc, Inc.
        r'\s+incorporated$',      # Incorporated
        r'\s+corp\.?$',          # Corp, Corp.
        r'\s+corporation$',       # Corporation
        r'\s+llc$',               # LLC
        r'\s+llp$',               # LLP
        r'\s+plc$',               # PLC
        r'\s+gmbh$',              # GmbH (German)
        r'\s+pty\s+limited$',    # Pty Limited
    ]
    
    import re
    for suffix_pattern in suffixes:
        normalized = re.sub(suffix_pattern, '', normalized)
    
    # Normalize whitespace (multiple spaces → single space)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def generate_job_hash(title, company, url, include_url=True):
    """
    Generate unique hash for job deduplication
    
    Args:
        title: Job title
        company: Company name (will be normalized)
        url: Job URL
        include_url: If True, include URL in hash (platform-specific dedup)
                    If False, hash only title+company (cross-platform dedup)
    
    Returns:
        SHA256 hash string
    """
    # Normalize company name for consistent matching
    company_normalized = normalize_company_name(company)
    
    if include_url:
        content = f"{title}|{company_normalized}|{url}".lower()
    else:
        # Cross-platform deduplication: ignore URL, hash only title+company
        content = f"{title}|{company_normalized}".lower()
    
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
    
    # Scores table - Extended for new scoring methods
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
            -- New columns for component-based scoring
            components TEXT,                    -- JSON array of component objects
            score_breakdown TEXT,              -- JSON object with score breakdown
            recommendation TEXT,               -- AI recommendation (APPLY/SKIP)
            -- New columns for hireability-based scoring
            hard_gate_failed TEXT,             -- Reason if hard gate failed (NULL if passed)
            risk_profile TEXT,                 -- JSON object with risk factors
            hireability_factors TEXT,          -- JSON array of hireability factors
            explanation TEXT,                  -- Detailed explanation
            -- Metadata
            scoring_method TEXT DEFAULT 'legacy', -- 'legacy', 'component_based', 'hireability_based'
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
    
    # Status History table - Track all status changes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    ''')
    
    # Interview Notes table - Track interviews
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            interview_date DATE NOT NULL,
            interview_type TEXT,
            interviewer_name TEXT,
            topics_discussed TEXT,
            questions_asked TEXT,
            my_performance TEXT,
            next_steps TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(job_id_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_search ON jobs(source_search_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_dates ON jobs(first_seen_date, is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_scores_job ON scores(job_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status_history_job ON status_history(job_id, changed_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_interview_notes_job ON interview_notes(job_id, interview_date)')
    
    # Migration: Add new columns to jobs table if they don't exist
    cursor.execute("PRAGMA table_info(jobs)")
    existing_job_columns = {row[1] for row in cursor.fetchall()}
    
    new_job_columns = {
        'interview_date': 'DATE',
        'interview_type': 'TEXT',
        'offer_date': 'DATE',
        'offer_amount': 'REAL',
        'offer_currency': 'TEXT DEFAULT "AUD"',
        'decision_date': 'DATE',
        'follow_up_date': 'DATE',
        'priority': 'INTEGER DEFAULT 0',
        'notes': 'TEXT'
    }
    
    for col_name, col_type in new_job_columns.items():
        if col_name not in existing_job_columns:
            cursor.execute(f'ALTER TABLE jobs ADD COLUMN {col_name} {col_type}')
            print(f"Added column {col_name} to jobs table")
    
    # Migration: Add new columns to scores table if they don't exist
    # Check and add component-based scoring columns
    try:
        cursor.execute("SELECT components FROM scores LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE scores ADD COLUMN components TEXT")
    
    try:
        cursor.execute("SELECT score_breakdown FROM scores LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE scores ADD COLUMN score_breakdown TEXT")
    
    try:
        cursor.execute("SELECT recommendation FROM scores LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE scores ADD COLUMN recommendation TEXT")
    
    # Check and add hireability-based scoring columns
    try:
        cursor.execute("SELECT hard_gate_failed FROM scores LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE scores ADD COLUMN hard_gate_failed TEXT")
    
    try:
        cursor.execute("SELECT risk_profile FROM scores LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE scores ADD COLUMN risk_profile TEXT")
    
    try:
        cursor.execute("SELECT hireability_factors FROM scores LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE scores ADD COLUMN hireability_factors TEXT")
    
    try:
        cursor.execute("SELECT explanation FROM scores LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE scores ADD COLUMN explanation TEXT")
    
    try:
        cursor.execute("SELECT scoring_method FROM scores LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE scores ADD COLUMN scoring_method TEXT DEFAULT 'legacy'")
    
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
    """Insert score for a job - Enhanced for new scoring methods"""
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
    
    # Determine scoring method
    scoring_method = score_data.get('scoring_method', 'legacy')
    
    # Handle new scoring method data structures
    components_json = None
    score_breakdown_json = None
    recommendation = None
    hard_gate_failed = None
    risk_profile_json = None
    hireability_factors_json = None
    explanation = None
    
    if scoring_method == 'hybrid':
        # Hybrid scoring data (combines component + hireability)
        components_json = json.dumps(score_data.get('components', []))
        score_breakdown_json = json.dumps(score_data.get('score_breakdown', {}))
        recommendation = score_data.get('recommendation')
        hard_gate_failed = score_data.get('hard_gate_failed')
        risk_profile_json = json.dumps(score_data.get('risk_profile', {}))
        hireability_factors_json = json.dumps(score_data.get('hireability_factors', {}))
        explanation = score_data.get('explanation')
        
    elif scoring_method == 'component_based':
        # Component-based scoring data
        components_json = json.dumps(score_data.get('components', []))
        score_breakdown_json = json.dumps(score_data.get('score_breakdown', {}))
        recommendation = score_data.get('recommendation')
        explanation = score_data.get('explanation')
        
    elif scoring_method == 'hireability_based':
        # Hireability-based scoring data
        hard_gate_failed = score_data.get('hard_gate_failed')
        risk_profile_json = json.dumps(score_data.get('risk_profile', {}))
        hireability_factors_json = json.dumps(score_data.get('hireability_factors', []))
        explanation = score_data.get('explanation')
        recommendation = score_data.get('recommendation')
        
        # For hireability scoring, also store score_breakdown if available
        if 'score_breakdown' in score_data:
            score_breakdown_json = json.dumps(score_data['score_breakdown'])
    
    cursor.execute('''
        INSERT INTO scores (
            job_id, score, reasoning, matched, not_matched, key_points, model_used, profile_hash,
            components, score_breakdown, recommendation, hard_gate_failed, risk_profile, 
            hireability_factors, explanation, scoring_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_id,
        score_data['score'],
        reasoning,
        matched_json,
        not_matched_json,
        key_points_json,
        score_data.get('model_used'),
        profile_hash,
        components_json,
        score_breakdown_json,
        recommendation,
        hard_gate_failed,
        risk_profile_json,
        hireability_factors_json,
        explanation,
        scoring_method
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
    """Get jobs above threshold that haven't been notified with all hybrid fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.*, 
               s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used,
               s.components, s.score_breakdown, s.recommendation, 
               s.hard_gate_failed, s.risk_profile, s.hireability_factors, 
               s.explanation, s.scoring_method
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
        job = _parse_job_hybrid_fields(job)
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


def _parse_job_hybrid_fields(job):
    """
    Parse all hybrid scoring JSON fields from a job dict
    
    Args:
        job: Job dict from database (with JSON strings)
    
    Returns:
        dict: Job dict with parsed JSON fields
    """
    import json
    
    # Legacy JSON fields (for backward compatibility)
    for field in ['matched', 'not_matched', 'key_points']:
        if job.get(field):
            try:
                job[field] = json.loads(job[field])
            except:
                job[field] = []
    
    # Hybrid scoring JSON fields
    if job.get('components'):
        try:
            job['components'] = json.loads(job['components'])
        except:
            job['components'] = []
    
    if job.get('score_breakdown'):
        try:
            job['score_breakdown'] = json.loads(job['score_breakdown'])
        except:
            job['score_breakdown'] = {}
    
    if job.get('risk_profile'):
        try:
            job['risk_profile'] = json.loads(job['risk_profile'])
        except:
            job['risk_profile'] = {}
    
    if job.get('hireability_factors'):
        try:
            job['hireability_factors'] = json.loads(job['hireability_factors'])
        except:
            job['hireability_factors'] = {}
    
    return job


def get_jobs_by_date_range(days, hide_old_days=30):
    """Get jobs within date range with all hybrid scoring fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    start_date = get_perth_date() - timedelta(days=days)
    hide_before = get_perth_date() - timedelta(days=hide_old_days)
    
    # Fetch all hybrid scoring fields
    cursor.execute('''
        SELECT j.*, 
               s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used,
               s.components, s.score_breakdown, s.recommendation, 
               s.hard_gate_failed, s.risk_profile, s.hireability_factors, 
               s.explanation, s.scoring_method
        FROM jobs j
        JOIN scores s ON j.id = s.job_id
        WHERE j.first_seen_date >= ?
        AND j.first_seen_date >= ?
        ORDER BY s.score DESC, j.first_seen_date DESC
    ''', (start_date, hide_before))
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        job = _parse_job_hybrid_fields(job)
        jobs.append(job)
    
    conn.close()
    return jobs


def get_all_jobs(include_inactive=False):
    """Get all jobs with all hybrid scoring fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch all hybrid scoring fields
    query = '''
        SELECT j.*, 
               s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used,
               s.components, s.score_breakdown, s.recommendation, 
               s.hard_gate_failed, s.risk_profile, s.hireability_factors, 
               s.explanation, s.scoring_method
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
        job = _parse_job_hybrid_fields(job)
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


def get_jobs_above_threshold(threshold, limit=None):
    """Get jobs scoring above threshold with details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT j.title, j.company, s.score
        FROM jobs j
        JOIN scores s ON j.id = s.job_id
        WHERE s.score >= ?
        ORDER BY s.score DESC, j.first_seen_date DESC
    '''
    
    if limit:
        query += f' LIMIT {limit}'
    
    cursor.execute(query, (threshold,))
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs


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
    """Get all applied jobs with all hybrid scoring fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.*, 
               s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used,
               s.components, s.score_breakdown, s.recommendation, 
               s.hard_gate_failed, s.risk_profile, s.hireability_factors, 
               s.explanation, s.scoring_method
        FROM jobs j
        LEFT JOIN scores s ON j.id = s.job_id
        WHERE j.applied = 1 AND j.rejected = 0
        ORDER BY j.applied_date DESC, j.first_seen_date DESC
    ''')
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        job = _parse_job_hybrid_fields(job)
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
    """Get all rejected jobs with all hybrid scoring fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.*, 
               s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used,
               s.components, s.score_breakdown, s.recommendation, 
               s.hard_gate_failed, s.risk_profile, s.hireability_factors, 
               s.explanation, s.scoring_method,
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
        job = _parse_job_hybrid_fields(job)
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


### ===================================================================
### APPLICATION TRACKING SYSTEM (ATS) FUNCTIONS
### ===================================================================

def update_job_status_with_history(job_id, new_status, notes=None):
    """
    Update job status and log to history
    
    Args:
        job_id: Job ID
        new_status: New status (interested, applied, responded, phone_screen, etc.)
        notes: Optional notes about the status change
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current status
    cursor.execute('SELECT status, applied FROM jobs WHERE id = ?', (job_id,))
    row = cursor.fetchone()
    old_status = row['status'] if row else None
    
    # Update job status
    cursor.execute('''
        UPDATE jobs
        SET status = ?
        WHERE id = ?
    ''', (new_status, job_id))
    
    # Log to history
    cursor.execute('''
        INSERT INTO status_history (job_id, old_status, new_status, notes)
        VALUES (?, ?, ?, ?)
    ''', (job_id, old_status, new_status, notes))
    
    # Update related fields based on status
    today = get_perth_date()
    if new_status == 'applied' and row and not row['applied']:
        cursor.execute('UPDATE jobs SET applied = 1, applied_date = ? WHERE id = ?', (today, job_id))
    elif new_status == 'offer_received':
        cursor.execute('UPDATE jobs SET offer_date = ? WHERE id = ?', (today, job_id))
    elif new_status in ['accepted', 'declined_offer', 'rejected']:
        cursor.execute('UPDATE jobs SET decision_date = ? WHERE id = ?', (today, job_id))
        if new_status == 'rejected':
            cursor.execute('UPDATE jobs SET rejected = 1, rejected_date = ? WHERE id = ?', (today, job_id))
    
    conn.commit()
    conn.close()
    print(f"Updated job {job_id} status: {old_status} -> {new_status}")


def get_status_history(job_id):
    """Get status change history for a job"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT old_status, new_status, changed_at, notes
        FROM status_history
        WHERE job_id = ?
        ORDER BY changed_at DESC
    ''', (job_id,))
    
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history


def get_jobs_by_status_filter(status):
    """Get all jobs with specific status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.*, 
               s.score, s.reasoning, s.matched, s.not_matched, s.key_points, s.model_used,
               s.components, s.score_breakdown, s.recommendation, 
               s.hard_gate_failed, s.risk_profile, s.hireability_factors, 
               s.explanation, s.scoring_method
        FROM jobs j
        LEFT JOIN scores s ON j.id = s.job_id
        WHERE j.status = ? AND j.is_active = 1
        ORDER BY s.score DESC, j.first_seen_date DESC
    ''', (status,))
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        job = _parse_job_hybrid_fields(job)
        jobs.append(job)
    
    conn.close()
    return jobs


def add_interview(job_id, interview_data):
    """
    Schedule/add interview for a job
    
    Args:
        job_id: Job ID
        interview_data: Dict with interview details
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO interview_notes (
            job_id, interview_date, interview_type, interviewer_name,
            topics_discussed, questions_asked, my_performance, next_steps, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_id,
        interview_data.get('interview_date'),
        interview_data.get('interview_type'),
        interview_data.get('interviewer_name'),
        interview_data.get('topics_discussed'),
        interview_data.get('questions_asked'),
        interview_data.get('my_performance'),
        interview_data.get('next_steps'),
        interview_data.get('notes')
    ))
    
    # Update job interview_date and interview_type
    cursor.execute('''
        UPDATE jobs
        SET interview_date = ?, interview_type = ?
        WHERE id = ?
    ''', (interview_data.get('interview_date'), interview_data.get('interview_type'), job_id))
    
    conn.commit()
    conn.close()
    print(f"Added interview for job {job_id}")


def get_interviews_for_job(job_id):
    """Get all interviews for a job"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT *
        FROM interview_notes
        WHERE job_id = ?
        ORDER BY interview_date DESC
    ''', (job_id,))
    
    interviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return interviews


def get_upcoming_interviews(days=30):
    """Get interviews in next N days"""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = get_perth_date()
    future_date = today + timedelta(days=days)
    
    cursor.execute('''
        SELECT i.*, j.title, j.company, j.url
        FROM interview_notes i
        JOIN jobs j ON i.job_id = j.id
        WHERE i.interview_date BETWEEN ? AND ?
        AND j.is_active = 1
        ORDER BY i.interview_date ASC
    ''', (today, future_date))
    
    interviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return interviews


def set_job_priority(job_id, priority):
    """
    Set job priority
    
    Args:
        job_id: Job ID
        priority: 0=normal, 1=high, 2=urgent
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE jobs SET priority = ? WHERE id = ?', (priority, job_id))
    
    conn.commit()
    conn.close()
    print(f"Set job {job_id} priority to {priority}")


def add_job_note(job_id, note):
    """Add or append note to job"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT notes FROM jobs WHERE id = ?', (job_id,))
    row = cursor.fetchone()
    
    existing_notes = row['notes'] if row and row['notes'] else ''
    today = get_perth_date()
    new_note = f"\n[{today}] {note}" if existing_notes else f"[{today}] {note}"
    updated_notes = existing_notes + new_note
    
    cursor.execute('UPDATE jobs SET notes = ? WHERE id = ?', (updated_notes, job_id))
    
    conn.commit()
    conn.close()
    print(f"Added note to job {job_id}")


def get_status_statistics():
    """Get job counts by status for analytics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            status,
            COUNT(*) as count
        FROM jobs
        WHERE is_active = 1
        GROUP BY status
        ORDER BY count DESC
    ''')
    
    stats = {row['status']: row['count'] for row in cursor.fetchall()}
    conn.close()
    return stats
