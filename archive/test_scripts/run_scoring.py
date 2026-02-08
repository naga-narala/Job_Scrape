#!/usr/bin/env python3
"""
Run AI scoring for unscored jobs using the actual workflow
Uses scorer.score_batch() with AI model fallback chain
"""

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import database as db
import scorer

def main():
    """Score all unscored jobs using AI scoring workflow"""
    
    # Load config
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Initialize database
    db.init_database()
    
    # Get unscored jobs
    unscored = db.get_unscored_jobs()
    
    if not unscored:
        print("\n✓ No unscored jobs found")
        return
    
    print(f"\n{'=' * 70}")
    print(f"🎯 AI SCORING WORKFLOW")
    print(f"{'=' * 70}")
    print(f"Unscored jobs: {len(unscored)}")
    print(f"Using AI models with fallback:")
    print(f"  1. {config.get('ai_models', {}).get('primary', 'N/A')}")
    print(f"  2. {config.get('ai_models', {}).get('secondary', 'N/A')}")
    print(f"  3. {config.get('ai_models', {}).get('tertiary', 'N/A')}")
    print(f"  4. Parser fallback (if all AI models fail)")
    print(f"\nStarting in 3 seconds...")
    
    import time
    time.sleep(3)
    
    # Load profile
    profile_content = scorer.load_profile()
    
    # Score using actual workflow function
    print(f"\n{'=' * 70}")
    print("⚡ SCORING IN PROGRESS")
    print(f"{'=' * 70}\n")
    
    score_summary = scorer.score_batch(
        unscored,
        profile_content,
        config.get('ai_models', {}),
        config.get('openrouter_api_key')
    )
    
    # Insert scores into database
    profile_hash = db.get_profile_hash()
    for score_data in score_summary.get('scores', []):
        if score_data.get('job_id'):
            db.insert_score(score_data['job_id'], score_data, profile_hash)
    
    # Display results
    print(f"\n{'=' * 70}")
    print("📊 SCORING COMPLETE")
    print(f"{'=' * 70}")
    print(f"✅ Successfully scored: {score_summary.get('scored', 0)}/{len(unscored)}")
    print(f"   🤖 AI scored: {score_summary.get('ai_scored', 0)}")
    print(f"   📝 Parser fallback: {score_summary.get('parser_scored', 0)}")
    if score_summary.get('failed', 0) > 0:
        print(f"   ❌ Failed: {score_summary.get('failed', 0)}")
    print(f"📊 Average score: {score_summary.get('avg_score', 0):.1f}%")
    
    # Show top matches
    all_jobs = db.get_all_jobs()
    top_jobs = sorted(all_jobs, key=lambda x: x.get('score', 0), reverse=True)[:10]
    
    if top_jobs:
        print(f"\n🏆 TOP 10 MATCHES:")
        for i, job in enumerate(top_jobs, 1):
            score = job.get('score', 0)
            emoji = '🟢' if score >= 70 else '🟡' if score >= 50 else '🔴'
            source_emoji = {'linkedin': '🔗', 'seek': '🔍', 'jora': '📋'}.get(job.get('source'), '❓')
            title = job['title'][:60]
            company = job.get('company', 'Unknown')[:25]
            print(f"   {i:2}. {emoji} {score}% {source_emoji} {title} ({company})")
    
    print(f"\n{'=' * 70}")
    print(f"🌐 View all jobs at: http://localhost:8000")
    print(f"⏰ Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

if __name__ == '__main__':
    main()
