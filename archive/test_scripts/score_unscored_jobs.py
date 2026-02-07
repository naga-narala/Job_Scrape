#!/usr/bin/env python3
"""
Quick script to assign default scores to unscored jobs
so they appear in the dashboard
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import database
import hashlib

def get_profile_hash():
    """Get hash of current profile"""
    try:
        with open('profile.txt', 'r') as f:
            return hashlib.md5(f.read().encode()).hexdigest()
    except:
        return 'default_profile'

def assign_default_scores():
    """Assign default 50% score to all unscored jobs"""
    
    print("📊 Assigning default scores to unscored jobs...\n")
    
    # Get all unscored jobs
    unscored = database.get_unscored_jobs()
    print(f"Found {len(unscored)} unscored jobs")
    
    if len(unscored) == 0:
        print("✓ All jobs already have scores!")
        return
    
    profile_hash = get_profile_hash()
    
    # Assign default score to each
    for i, job in enumerate(unscored, 1):
        score_data = {
            'score': 50,  # Default neutral score
            'matched': ['Job awaiting detailed AI scoring'],
            'not_matched': [],
            'key_points': ['Preliminary score - needs AI review'],
            'model_used': 'default-placeholder'
        }
        
        database.insert_score(
            job_id=job['job_id_hash'],
            score_data=score_data,
            profile_hash=profile_hash
        )
        
        title = job['title'][:60]
        print(f"  [{i}/{len(unscored)}] ✓ Scored: {title}... (50%)")
    
    print(f"\n✅ Successfully assigned default scores to {len(unscored)} jobs")
    print(f"🌐 View them at: http://localhost:8000")
    print(f"\nNote: These are placeholder scores. Run AI scoring later for accurate matches.")

if __name__ == "__main__":
    try:
        assign_default_scores()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
