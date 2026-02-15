"""
AI Job Scoring with Database Integration
Tests intelligent component extraction AND stores results in beautiful database

Integration: Connects test_combined_scoring.py with scoring_database.py
"""

import sys
import os
import json
import time
import random
import sqlite3
import hashlib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scoring_database import (
    start_scoring_session,
    insert_job_score,
    complete_scoring_session,
    export_session_to_json,
    get_session_results,
    get_top_scoring_jobs,
    get_component_statistics
)

# Import the scoring logic from test file
sys.path.insert(0, str(Path(__file__).parent))
from test_combined_scoring import call_combined_scoring_api, display_combined_result


def get_profile_hash():
    """Calculate MD5 hash of profile.txt"""
    profile_path = Path(__file__).parent.parent / 'profile.txt'
    with open(profile_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return hashlib.md5(content.encode()).hexdigest()


def load_jobs_from_db(limit=10):
    """Load random jobs from main jobs.db"""
    db_path = Path(__file__).parent.parent / 'data' / 'jobs.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT j.*, j.id as job_db_id
        FROM jobs j
        LEFT JOIN scores s ON j.job_id_hash = s.job_id
        WHERE s.job_id IS NULL
        ORDER BY RANDOM()
        LIMIT ?
    ''', (limit,))
    
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jobs


def score_and_store_jobs(num_jobs=10, model=None):
    """
    Score jobs using intelligent extraction and store in database
    
    Args:
        num_jobs: Number of jobs to score
        model: AI model to use (from config)
    
    Returns: session_id
    """
    print(f"\n{'='*80}")
    print(f"🎯 AI JOB SCORING WITH DATABASE STORAGE")
    print(f"{'='*80}\n")
    
    # Load configuration
    config_path = Path(__file__).parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    import sqlite3
    import json
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    import scorer
    import database

    JOBS_DB = Path(__file__).parent.parent / 'data' / 'jobs.db'
    SCORING_DB = Path(__file__).parent.parent / 'data' / 'ai_scoring_results.db'

    def merge_scoring_db():
        """
        Merge ai_scoring_results.db job_scores and score_components into jobs.db scores table.
        All component/insight data is stored as JSON in scores.components, scores.key_points, etc.
        """
        jobs_conn = sqlite3.connect(str(JOBS_DB))
        scoring_conn = sqlite3.connect(str(SCORING_DB))
        jobs_cur = jobs_conn.cursor()
        scoring_cur = scoring_conn.cursor()

        # Get all job_scores
        scoring_cur.execute("SELECT * FROM job_scores LIMIT 20")
        job_scores = scoring_cur.fetchall()
        columns = [desc[0] for desc in scoring_cur.description]

        for row in job_scores:
            score_dict = dict(zip(columns, row))
            job_id_hash = score_dict['job_id_hash']
            # Find job_id in jobs.db
            jobs_cur.execute("SELECT id FROM jobs WHERE job_id_hash=?", (job_id_hash,))
            job_row = jobs_cur.fetchone()
            if not job_row:
                continue
            job_id = job_row[0]

            # Get score_components for this score
            scoring_cur.execute("SELECT * FROM score_components WHERE score_id=?", (score_dict['score_id'],))
            comp_rows = scoring_cur.fetchall()
            comp_cols = [desc[0] for desc in scoring_cur.description]
            components = [dict(zip(comp_cols, comp)) for comp in comp_rows]

            # Get scoring_insights for this score
            scoring_cur.execute("SELECT insight_text FROM scoring_insights WHERE score_id=? ORDER BY insight_order", (score_dict['score_id'],))
            insights = [r[0] for r in scoring_cur.fetchall()]

            # Prepare score data for jobs.db
            score_data = {
                'score': int(score_dict.get('total_score', 0)),
                'reasoning': score_dict.get('hard_gate_reason', ''),
                'matched': [],
                'not_matched': [],
                'key_points': insights,
                'model_used': score_dict.get('model_used', ''),
                'profile_hash': score_dict.get('session_id', ''),
                'components': json.dumps(components),
                'score_breakdown': score_dict.get('components_json', ''),
                'recommendation': score_dict.get('recommendation', ''),
                'hard_gate_failed': score_dict.get('hard_gate_failed', ''),
                'risk_profile': score_dict.get('risk_profile_json', ''),
                'hireability_factors': '',
                'explanation': score_dict.get('hard_gate_reason', ''),
                'scoring_method': score_dict.get('scoring_method', 'intelligent_extraction')
            }
            # Insert into scores table
            jobs_cur.execute("INSERT OR REPLACE INTO scores (job_id, score, reasoning, matched, not_matched, key_points, model_used, profile_hash, components, score_breakdown, recommendation, hard_gate_failed, risk_profile, hireability_factors, explanation, scoring_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (job_id, score_data['score'], score_data['reasoning'], json.dumps(score_data['matched']), json.dumps(score_data['not_matched']), json.dumps(score_data['key_points']), score_data['model_used'], score_data['profile_hash'], score_data['components'], score_data['score_breakdown'], score_data['recommendation'], score_data['hard_gate_failed'], score_data['risk_profile'], score_data['hireability_factors'], score_data['explanation'], score_data['scoring_method'])
            )
        jobs_conn.commit()
        jobs_conn.close()
        scoring_conn.close()
        print("✅ Merge complete: ai_scoring_results.db → jobs.db")

    def rescore_and_print():
        """
        Rescore 20 jobs from jobs.db using scorer.py and print all scoring details.
        """
        jobs = database.get_unscored_jobs()[:20]
        profile_content = scorer.load_profile()
        config = scorer.SCORER_CONFIG
        models_config = config.get('ai', {}).get('models', {})
        api_key = config.get('api_key', '')
        results = []
        for job in jobs:
            score_data = scorer.score_job_with_fallback(job, profile_content, models_config, api_key)
            results.append((job, score_data))
            # Insert score into DB
            database.insert_score(job['id'], score_data, profile_content)
        # Print results
        for job, score_data in results:
            print("\n═══════════════════════════════════════════════════════════════════")
            print(f"Job: {job['title']} | Company: {job['company']} | URL: {job['url']}")
            print(f"Score: {score_data.get('score', 0)} | Model: {score_data.get('model_used', '')}")
            print(f"Recommendation: {score_data.get('recommendation', '')}")
            print(f"Components:")
            comps = score_data.get('components', [])
            if isinstance(comps, str):
                try:
                    comps = json.loads(comps)
                except:
                    comps = []
            for comp in comps:
                print(f"  - {comp.get('component_name', '')}: {comp.get('component_score', '')} ({comp.get('match_status', '')})")
            print(f"AI Insights:")
            for insight in score_data.get('key_points', []):
                print(f"  • {insight}")
        print("\n✅ Rescoring and display complete.")

    # Load profile
    profile_path = Path(__file__).parent.parent / 'profile.txt'
    print("\n--- MERGING SCORING DB ---")
    merge_scoring_db()
    print("\n--- RESCORING 20 JOBS ---")
    rescore_and_print()
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile_content = f.read()
    
    # Load jobs.txt for context
    jobs_txt_path = Path(__file__).parent.parent / 'jobs.txt'
    with open(jobs_txt_path, 'r', encoding='utf-8') as f:
        jobs_txt_content = f.read()
    
    # Get model from config if not specified
    if model is None:
        model = config.get('ai', {}).get('models', {}).get('primary', 'anthropic/claude-3.5-haiku')
    
    api_key = config.get('openrouter_api_key')
    if not api_key:
        print("❌ Error: No OpenRouter API key in config.json")
        return None
    
    # Start scoring session
    profile_hash = get_profile_hash()
    session_id = start_scoring_session(
        model_used=model,
        scoring_method='intelligent_extraction',
        profile_hash=profile_hash,
        config={
            'model': model,
            'num_jobs': num_jobs,
            'profile_hash': profile_hash
        }
    )
    
    print(f"✅ Started scoring session: {session_id}")
    print(f"   Model: {model}")
    print(f"   Profile hash: {profile_hash[:8]}...")
    print(f"   Jobs to score: {num_jobs}\n")
    
    # Load jobs
    jobs = load_jobs_from_db(limit=num_jobs)
    
    if not jobs:
        print("❌ No unscored jobs found in database")
        return None
    
    print(f"📋 Loaded {len(jobs)} unscored jobs from database\n")
    
    # Score each job
    scored_count = 0
    failed_count = 0
    hard_gate_failures = 0
    total_score_sum = 0
    total_api_time = 0
    
    recommendation_counts = {'APPLY': 0, 'CONSIDER': 0, 'MAYBE': 0, 'SKIP': 0}
    
    for i, job in enumerate(jobs, 1):
        try:
            print(f"\n{'─'*80}")
            print(f"Job {i}/{len(jobs)}: {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Source: {job.get('source', 'unknown')}")
            print(f"{'─'*80}")
            
            # Call AI scoring
            start_time = time.time()
            result = call_combined_scoring_api(
                job,
                profile_content,
                jobs_txt_content,
                config
            )
            api_time_ms = int((time.time() - start_time) * 1000)
            total_api_time += api_time_ms
            
            if not result:
                print(f"❌ Failed to score job")
                failed_count += 1
                continue
            
            # Display result (simplified - just print summary)
            if result.get('hard_gate_failed'):
                print(f"\n⛔ HARD GATE REJECTION: {result['hard_gate_failed']}")
                print(f"   Insights: {', '.join(result.get('key_insights', [])[:2])}")
            else:
                score = result.get('total_score', 0)
                rec = result.get('recommendation', 'UNKNOWN')
                components = result.get('components', [])
                
                print(f"\n✅ Score: {score:.1f}/100 | Recommendation: {rec}")
                print(f"   Components: {len(components)}")
                print(f"   Weight Sum: {result.get('total_weight_verification', 0)}%")
                
                # Top 3 components
                if components:
                    print(f"\n   Top Components:")
                    for comp in sorted(components, key=lambda x: x['component_contribution'], reverse=True)[:3]:
                        print(f"      • {comp['name']} ({comp['weight']}%): {comp['component_score']}/100 = {comp['component_contribution']:.1f}")
                
                # Key insights
                insights = result.get('key_insights', [])
                if insights:
                    print(f"\n   Key Insights:")
                    for insight in insights[:3]:
                        print(f"      💡 {insight}")

            
            # Prepare job data for database
            job_data = {
                'job_id_hash': job.get('job_id_hash', ''),
                'title': job['title'],
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'source': job.get('source', ''),
                'url': job.get('url', '')
            }
            
            # Prepare metadata
            metadata = {
                'model_used': model,
                'scoring_method': 'intelligent_extraction',
                'api_latency_ms': api_time_ms,
                'tokens_used': None,  # Could be extracted from API response if available
                'cost_estimate_usd': None  # Could be calculated based on model pricing
            }
            
            # Insert into database
            score_id = insert_job_score(session_id, job_data, result, metadata)
            
            print(f"\n✅ Stored in database (score_id: {score_id})")
            
            scored_count += 1
            
            # Track statistics
            if result.get('hard_gate_failed'):
                hard_gate_failures += 1
            else:
                total_score_sum += result.get('total_score', 0)
                recommendation = result.get('recommendation', 'UNKNOWN')
                if recommendation in recommendation_counts:
                    recommendation_counts[recommendation] += 1
            
            # Rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error scoring job: {e}")
            failed_count += 1
            continue
    
    # Calculate statistics
    avg_score = total_score_sum / max(1, scored_count - hard_gate_failures)
    avg_api_time = total_api_time / max(1, scored_count)
    
    # Complete session
    stats = {
        'total_jobs_scored': scored_count,
        'total_api_calls': scored_count,
        'total_cost_usd': 0.0,  # Could be calculated
        'average_score': avg_score
    }
    
    complete_scoring_session(session_id, stats)
    
    # Print summary
    print(f"\n\n{'='*80}")
    print(f"📊 SCORING SESSION COMPLETE")
    print(f"{'='*80}")
    print(f"Session ID: {session_id}")
    print(f"Jobs scored: {scored_count}/{len(jobs)}")
    print(f"Failed: {failed_count}")
    print(f"Hard gate failures: {hard_gate_failures}")
    print(f"Average score: {avg_score:.1f}/100")
    print(f"Average API time: {avg_api_time:.0f}ms")
    print(f"\n📈 Recommendations:")
    for rec, count in recommendation_counts.items():
        if count > 0:
            print(f"   {rec}: {count}")
    
    # Export to JSON
    print(f"\n💾 Exporting results to JSON...")
    export_path = export_session_to_json(session_id)
    print(f"   File: {export_path}")
    
    return session_id


def view_session_results(session_id):
    """View detailed results from a session"""
    print(f"\n{'='*80}")
    print(f"📊 SESSION {session_id} RESULTS")
    print(f"{'='*80}\n")
    
    results = get_session_results(session_id)
    session = results['session']
    jobs = results['jobs']
    
    print(f"Session Info:")
    print(f"   Started: {session['session_started_at']}")
    print(f"   Completed: {session['session_completed_at']}")
    print(f"   Model: {session['model_used']}")
    print(f"   Method: {session['scoring_method']}")
    print(f"   Total jobs: {session['total_jobs_scored']}")
    print(f"   Average score: {session['average_score']:.1f}/100")
    
    print(f"\n🏆 Top Scoring Jobs:\n")
    
    for i, job in enumerate(jobs[:10], 1):
        score = job['total_score']
        rec = job['recommendation']
        
        # Color coding
        if score >= 75:
            icon = "🟢"
        elif score >= 60:
            icon = "🟡"
        else:
            icon = "🔴"
        
        print(f"{i}. {icon} {job['job_title']} - {job['job_company']}")
        print(f"   Score: {score:.1f}/100 | Recommendation: {rec}")
        print(f"   Components: {job['components_count']}")
        
        # Show top 3 components
        components = job.get('components_detailed', [])[:3]
        if components:
            print(f"   Top Components:")
            for comp in components:
                print(f"      • {comp['component_name']} ({comp['component_weight']}%): {comp['component_score']}/100")
        
        print()


def analyze_components(session_id=None):
    """Analyze component statistics"""
    print(f"\n{'='*80}")
    print(f"📊 COMPONENT ANALYSIS")
    print(f"{'='*80}\n")
    
    stats = get_component_statistics(session_id)
    
    print(f"Category Breakdown:\n")
    
    for i, stat in enumerate(stats[:15], 1):
        print(f"{i}. {stat['component_category']}")
        print(f"   Count: {stat['count']}")
        print(f"   Avg Weight: {stat['avg_weight']:.1f}%")
        print(f"   Avg Score: {stat['avg_score']:.1f}/100")
        print(f"   Avg Contribution: {stat['avg_contribution']:.1f}")
        print()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Job Scoring with Database Storage')
    parser.add_argument('--num-jobs', type=int, default=10, help='Number of jobs to score')
    parser.add_argument('--model', type=str, help='AI model to use')
    parser.add_argument('--view-session', type=int, help='View results from session ID')
    parser.add_argument('--analyze-components', action='store_true', help='Analyze component statistics')
    parser.add_argument('--top-jobs', type=int, help='Show top N scoring jobs across all sessions')
    
    args = parser.parse_args()
    
    if args.view_session:
        view_session_results(args.view_session)
    elif args.analyze_components:
        analyze_components()
    elif args.top_jobs:
        print(f"\n🏆 Top {args.top_jobs} Scoring Jobs (All Sessions):\n")
        jobs = get_top_scoring_jobs(limit=args.top_jobs)
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['job_title']} - {job['job_company']}")
            print(f"   Score: {job['total_score']:.1f}/100 | {job['recommendation']}")
            print(f"   Components: {job['components_count']}")
            print()
    else:
        # Score new jobs
        session_id = score_and_store_jobs(num_jobs=args.num_jobs, model=args.model)
        
        if session_id:
            print(f"\n✅ All results saved to database!")
            print(f"\n💡 View results with:")
            print(f"   python score_testing/test_combined_with_db.py --view-session {session_id}")
            print(f"\n💡 Analyze components:")
            print(f"   python score_testing/test_combined_with_db.py --analyze-components")


    # (Removed old main/CLI logic. Now only merge/rescore logic runs.)
