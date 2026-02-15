"""
Compare Legacy scorer.py vs. Component-Based Scorer (test_combined_scoring.py)
Outputs side-by-side results for the same jobs.
"""

import sys
import json
from pathlib import Path
import time

# Add src and score_testing to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

import sqlite3

# Import legacy scorer
import scorer
# Import component-based scorer
from test_combined_scoring import call_combined_scoring_api

def load_jobs_from_db(limit=5):
    db_path = Path(__file__).parent.parent / 'data' / 'jobs.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM jobs
        ORDER BY RANDOM()
        LIMIT ?
    ''', (limit,))
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs

def main():
    # Load config and profile
    config_path = Path(__file__).parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    profile_content = scorer.load_profile()
    jobs_txt_path = Path(__file__).parent.parent / 'jobs.txt'
    with open(jobs_txt_path, 'r', encoding='utf-8') as f:
        jobs_txt_content = f.read()
    models_config = config.get('ai', {}).get('models', {})
    api_key = config.get('openrouter_api_key') or config.get('api_key')
    if not api_key:
        print("❌ No OpenRouter API key in config.json")
        return

    jobs = load_jobs_from_db(limit=5)
    print(f"\nComparing scorers on {len(jobs)} jobs...\n")
    for idx, job in enumerate(jobs, 1):
        print(f"{'='*90}")
        print(f"Job {idx}: {job['title']} at {job.get('company', '')}")
        print(f"URL: {job.get('url', '')}")
        print(f"{'-'*90}")
        # Legacy scorer
        legacy = scorer.score_job_with_fallback(job, profile_content, models_config, api_key)
        # Component-based scorer
        combined = call_combined_scoring_api(job, profile_content, jobs_txt_content, config)
        # Print side by side
        print(f"LEGACY SCORER (scorer.py):")
        print(f"  Score: {legacy.get('score', '')}")
        print(f"  Model: {legacy.get('model_used', '')}")
        print(f"  Matched: {legacy.get('matched', [])}")
        print(f"  Not Matched: {legacy.get('not_matched', [])}")
        print(f"  Key Points: {legacy.get('key_points', [])}")
        print(f"  Recommendation: {legacy.get('recommendation', '') if 'recommendation' in legacy else 'N/A'}")
        print()
        print(f"COMPONENT SCORER (test_combined_scoring.py):")
        print(f"  Score: {combined.get('total_score', '')}")
        print(f"  Model: {combined.get('model_used', '')}")
        print(f"  Recommendation: {combined.get('recommendation', '')}")
        print(f"  Hard Gate Failed: {combined.get('hard_gate_failed', '')}")
        print(f"  Components:")
        for comp in combined.get('components', [])[:5]:
            print(f"    - {comp.get('name', '')}: {comp.get('component_score', '')}/100 (weight: {comp.get('weight', '')}%) [{comp.get('match_status', '')}]")
        print(f"  Key Insights: {combined.get('key_insights', [])}")
        print()
        time.sleep(1)

if __name__ == '__main__':
    main()
