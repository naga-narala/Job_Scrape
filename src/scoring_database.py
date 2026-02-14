"""
AI Scoring Results Database - Beautiful JSON Storage
Stores comprehensive AI job scoring analysis with full component breakdown

Created: 2026-02-14
Purpose: Store detailed AI scoring results with component-level analysis
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import pytz

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'ai_scoring_results.db'


def get_perth_now():
    """Get current datetime in Perth timezone"""
    perth_tz = pytz.timezone('Australia/Perth')
    return datetime.now(perth_tz)


def init_scoring_database():
    """
    Initialize beautiful AI scoring database with comprehensive schema
    
    Tables:
    1. scoring_sessions - Track each scoring run
    2. job_scores - Store job-level scores with full JSON
    3. score_components - Individual component breakdown
    4. scoring_insights - Key insights from AI analysis
    5. scoring_metadata - Track model performance and costs
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Table 1: Scoring Sessions (track each run)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scoring_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_started_at TIMESTAMP NOT NULL,
            session_completed_at TIMESTAMP,
            model_used TEXT NOT NULL,
            scoring_method TEXT DEFAULT 'intelligent_extraction',
            total_jobs_scored INTEGER DEFAULT 0,
            total_api_calls INTEGER DEFAULT 0,
            total_cost_usd REAL DEFAULT 0.0,
            average_score REAL,
            profile_hash TEXT,
            config_snapshot TEXT,
            status TEXT DEFAULT 'running',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table 2: Job Scores (main results with full JSON)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_scores (
            score_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            job_id_hash TEXT NOT NULL,
            job_title TEXT NOT NULL,
            job_company TEXT,
            job_location TEXT,
            job_source TEXT,
            job_url TEXT,
            
            -- Hard gate results
            hard_gate_failed TEXT,
            hard_gate_reason TEXT,
            
            -- Overall scoring
            total_score REAL NOT NULL,
            total_weight_verification INTEGER,
            recommendation TEXT,
            
            -- Full AI response (complete JSON)
            full_ai_response TEXT NOT NULL,
            
            -- Components summary
            components_count INTEGER,
            components_json TEXT,
            
            -- Insights
            key_insights_json TEXT,
            
            -- Risk profile (if available)
            risk_profile_json TEXT,
            
            -- Evidence tracking
            matched_evidence_json TEXT,
            gap_analysis_json TEXT,
            
            -- Metadata
            model_used TEXT NOT NULL,
            scoring_method TEXT DEFAULT 'intelligent_extraction',
            api_latency_ms INTEGER,
            tokens_used INTEGER,
            cost_estimate_usd REAL,
            
            -- Timestamps
            scored_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (session_id) REFERENCES scoring_sessions(session_id) ON DELETE CASCADE
        )
    ''')
    
    # Table 3: Score Components (detailed component breakdown)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS score_components (
            component_id INTEGER PRIMARY KEY AUTOINCREMENT,
            score_id INTEGER NOT NULL,
            
            -- Component details
            component_name TEXT NOT NULL,
            component_category TEXT,
            component_weight INTEGER NOT NULL,
            component_score INTEGER NOT NULL,
            component_contribution REAL NOT NULL,
            match_status TEXT,
            
            -- Evidence
            evidence_from_profile TEXT,
            evidence_from_job TEXT,
            gap_analysis TEXT,
            
            -- Metadata
            component_rank INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (score_id) REFERENCES job_scores(score_id) ON DELETE CASCADE
        )
    ''')
    
    # Table 4: Scoring Insights (key insights per job)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scoring_insights (
            insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            score_id INTEGER NOT NULL,
            insight_text TEXT NOT NULL,
            insight_type TEXT,
            insight_order INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (score_id) REFERENCES job_scores(score_id) ON DELETE CASCADE
        )
    ''')
    
    # Table 5: Scoring Metadata (performance tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scoring_metadata (
            metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            
            -- Performance metrics
            jobs_per_minute REAL,
            average_api_latency_ms INTEGER,
            total_tokens_used INTEGER,
            
            -- Quality metrics
            hard_gate_rejection_rate REAL,
            average_component_count REAL,
            weight_validation_pass_rate REAL,
            
            -- Cost tracking
            total_cost_usd REAL,
            cost_per_job_usd REAL,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (session_id) REFERENCES scoring_sessions(session_id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_scores_session ON job_scores(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_scores_hash ON job_scores(job_id_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_scores_score ON job_scores(total_score)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_scores_recommendation ON job_scores(recommendation)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_components_score ON score_components(score_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_components_category ON score_components(component_category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_score ON scoring_insights(score_id)')
    
    conn.commit()
    conn.close()
    print(f"✅ AI Scoring Database initialized: {DB_PATH}")


def start_scoring_session(model_used, scoring_method, profile_hash, config=None):
    """
    Start a new scoring session
    
    Returns: session_id
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    config_snapshot = json.dumps(config) if config else None
    
    cursor.execute('''
        INSERT INTO scoring_sessions (
            session_started_at, model_used, scoring_method, profile_hash, config_snapshot, status
        ) VALUES (?, ?, ?, ?, ?, 'running')
    ''', (get_perth_now(), model_used, scoring_method, profile_hash, config_snapshot))
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return session_id


def insert_job_score(session_id, job_data, ai_response, metadata=None):
    """
    Insert comprehensive job score with full AI analysis
    
    Args:
        session_id: Active session ID
        job_data: Job information dict
        ai_response: Full AI response dict
        metadata: Optional metadata (latency, tokens, etc.)
    
    Returns: score_id
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Extract metadata
    metadata = metadata or {}
    
    # Insert main score record
    cursor.execute('''
        INSERT INTO job_scores (
            session_id, job_id_hash, job_title, job_company, job_location, job_source, job_url,
            hard_gate_failed, hard_gate_reason,
            total_score, total_weight_verification, recommendation,
            full_ai_response, components_count, components_json, key_insights_json,
            risk_profile_json,
            model_used, scoring_method, api_latency_ms, tokens_used, cost_estimate_usd,
            scored_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        job_data.get('job_id_hash', ''),
        job_data.get('title', 'Unknown'),
        job_data.get('company', ''),
        job_data.get('location', ''),
        job_data.get('source', ''),
        job_data.get('url', ''),
        ai_response.get('hard_gate_failed'),
        ai_response.get('hard_gate_failed'),  # reason same as failed flag for now
        ai_response.get('total_score', 0),
        ai_response.get('total_weight_verification', 0),
        ai_response.get('recommendation', 'UNKNOWN'),
        json.dumps(ai_response),
        len(ai_response.get('components', [])),
        json.dumps(ai_response.get('components', [])),
        json.dumps(ai_response.get('key_insights', [])),
        json.dumps(ai_response.get('risk_profile', {})),
        metadata.get('model_used', 'unknown'),
        metadata.get('scoring_method', 'intelligent_extraction'),
        metadata.get('api_latency_ms'),
        metadata.get('tokens_used'),
        metadata.get('cost_estimate_usd'),
        get_perth_now()
    ))
    
    score_id = cursor.lastrowid
    
    # Insert components
    components = ai_response.get('components', [])
    for rank, component in enumerate(components, 1):
        cursor.execute('''
            INSERT INTO score_components (
                score_id, component_name, component_category, component_weight,
                component_score, component_contribution, match_status,
                evidence_from_profile, evidence_from_job, gap_analysis, component_rank
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            score_id,
            component.get('name', 'Unknown'),
            component.get('category', ''),
            component.get('weight', 0),
            component.get('component_score', 0),
            component.get('component_contribution', 0),
            component.get('match_status', ''),
            component.get('evidence_from_profile', ''),
            component.get('evidence_from_job', ''),
            component.get('gap_analysis', ''),
            rank
        ))
    
    # Insert key insights
    insights = ai_response.get('key_insights', [])
    for order, insight in enumerate(insights, 1):
        cursor.execute('''
            INSERT INTO scoring_insights (score_id, insight_text, insight_order)
            VALUES (?, ?, ?)
        ''', (score_id, insight, order))
    
    conn.commit()
    conn.close()
    
    return score_id


def complete_scoring_session(session_id, stats=None):
    """
    Mark scoring session as complete and update statistics
    
    Args:
        session_id: Session ID to complete
        stats: Optional statistics dict
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    stats = stats or {}
    
    cursor.execute('''
        UPDATE scoring_sessions
        SET session_completed_at = ?,
            total_jobs_scored = ?,
            total_api_calls = ?,
            total_cost_usd = ?,
            average_score = ?,
            status = 'completed'
        WHERE session_id = ?
    ''', (
        get_perth_now(),
        stats.get('total_jobs_scored', 0),
        stats.get('total_api_calls', 0),
        stats.get('total_cost_usd', 0.0),
        stats.get('average_score', 0.0),
        session_id
    ))
    
    conn.commit()
    conn.close()


def get_session_results(session_id):
    """
    Get all results for a scoring session
    
    Returns: dict with session info and all job scores
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get session info
    cursor.execute('SELECT * FROM scoring_sessions WHERE session_id = ?', (session_id,))
    session = dict(cursor.fetchone())
    
    # Get all job scores
    cursor.execute('''
        SELECT * FROM job_scores 
        WHERE session_id = ? 
        ORDER BY total_score DESC
    ''', (session_id,))
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        
        # Parse JSON fields
        job['full_ai_response'] = json.loads(job['full_ai_response'])
        job['components'] = json.loads(job['components_json']) if job['components_json'] else []
        job['key_insights'] = json.loads(job['key_insights_json']) if job['key_insights_json'] else []
        job['risk_profile'] = json.loads(job['risk_profile_json']) if job['risk_profile_json'] else {}
        
        # Get components
        cursor.execute('''
            SELECT * FROM score_components 
            WHERE score_id = ? 
            ORDER BY component_rank
        ''', (job['score_id'],))
        job['components_detailed'] = [dict(r) for r in cursor.fetchall()]
        
        # Get insights
        cursor.execute('''
            SELECT * FROM scoring_insights 
            WHERE score_id = ? 
            ORDER BY insight_order
        ''', (job['score_id'],))
        job['insights_detailed'] = [dict(r) for r in cursor.fetchall()]
        
        jobs.append(job)
    
    conn.close()
    
    return {
        'session': session,
        'jobs': jobs,
        'total_jobs': len(jobs)
    }


def export_session_to_json(session_id, output_path=None):
    """
    Export complete session results to beautiful JSON file
    
    Args:
        session_id: Session to export
        output_path: Optional custom output path
    
    Returns: Path to exported file
    """
    if output_path is None:
        output_dir = Path(__file__).parent.parent / 'data' / 'scoring_exports'
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = get_perth_now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f'ai_scoring_session_{session_id}_{timestamp}.json'
    
    results = get_session_results(session_id)
    
    # Write beautiful formatted JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported session {session_id} to: {output_path}")
    return str(output_path)


def get_top_scoring_jobs(session_id=None, limit=10, min_score=None):
    """
    Get top scoring jobs (optionally filtered by session and score)
    
    Args:
        session_id: Optional session filter
        limit: Number of results
        min_score: Optional minimum score filter
    
    Returns: List of job dicts with scores
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM job_scores WHERE 1=1'
    params = []
    
    if session_id:
        query += ' AND session_id = ?'
        params.append(session_id)
    
    if min_score is not None:
        query += ' AND total_score >= ?'
        params.append(min_score)
    
    query += ' ORDER BY total_score DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        job['full_ai_response'] = json.loads(job['full_ai_response'])
        job['components'] = json.loads(job['components_json']) if job['components_json'] else []
        job['key_insights'] = json.loads(job['key_insights_json']) if job['key_insights_json'] else []
        jobs.append(job)
    
    conn.close()
    return jobs


def get_component_statistics(session_id=None):
    """
    Get statistics about components across all jobs
    
    Returns: Dict with component analysis
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
        SELECT 
            component_category,
            COUNT(*) as count,
            AVG(component_weight) as avg_weight,
            AVG(component_score) as avg_score,
            AVG(component_contribution) as avg_contribution
        FROM score_components
    '''
    
    if session_id:
        query += ' WHERE score_id IN (SELECT score_id FROM job_scores WHERE session_id = ?)'
        cursor.execute(query + ' GROUP BY component_category ORDER BY count DESC', (session_id,))
    else:
        cursor.execute(query + ' GROUP BY component_category ORDER BY count DESC')
    
    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return stats


def search_jobs_by_component(component_name, min_score=None, session_id=None):
    """
    Find jobs that have a specific component
    
    Args:
        component_name: Component to search for
        min_score: Optional minimum component score
        session_id: Optional session filter
    
    Returns: List of matching jobs
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
        SELECT DISTINCT js.* 
        FROM job_scores js
        JOIN score_components sc ON js.score_id = sc.score_id
        WHERE sc.component_name LIKE ?
    '''
    params = [f'%{component_name}%']
    
    if min_score is not None:
        query += ' AND sc.component_score >= ?'
        params.append(min_score)
    
    if session_id:
        query += ' AND js.session_id = ?'
        params.append(session_id)
    
    query += ' ORDER BY js.total_score DESC'
    
    cursor.execute(query, params)
    
    jobs = []
    for row in cursor.fetchall():
        job = dict(row)
        job['components'] = json.loads(job['components_json']) if job['components_json'] else []
        jobs.append(job)
    
    conn.close()
    return jobs


if __name__ == '__main__':
    # Initialize database
    init_scoring_database()
    
    print("\n✅ AI Scoring Database Ready!")
    print(f"   Location: {DB_PATH}")
    print("\n📊 Database Schema:")
    print("   • scoring_sessions - Track each scoring run")
    print("   • job_scores - Job-level scores with full JSON")
    print("   • score_components - Component breakdown")
    print("   • scoring_insights - Key insights")
    print("   • scoring_metadata - Performance metrics")
    print("\n🎯 Example Usage:")
    print("   from scoring_database import *")
    print("   session_id = start_scoring_session('claude-3.5-sonnet', 'intelligent_extraction', 'hash123')")
    print("   score_id = insert_job_score(session_id, job_data, ai_response)")
    print("   export_session_to_json(session_id)")
