#!/usr/bin/env python3
"""Quick test of scoring methods on 1 job"""
import sys
import json
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import scorer

# Load config
config_path = Path(__file__).parent / 'config.json'
with open(config_path, 'r') as f:
    config = json.load(f)

# Get one job
conn = sqlite3.connect('data/jobs.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT * FROM jobs WHERE description IS NOT NULL LIMIT 1')
job = dict(cursor.fetchone())
conn.close()

print(f"\n🎯 Testing on job: {job['title'][:60]}")
print(f"Company: {job.get('company', 'Unknown')}")

# Load profile
profile = scorer.load_profile()
api_key = config.get('openrouter_api_key')

# Test legacy
print(f"\n1️⃣ Testing LEGACY scoring...")
legacy_models = config.get('ai', {}).get('models', {})
try:
    result = scorer.score_job_with_fallback(job, profile, legacy_models, api_key)
    print(f"✅ Legacy: {result.get('score')}% using {result.get('model_used')}")
except Exception as e:
    print(f"❌ Legacy failed: {e}")

# Test component-based with Claude
print(f"\n2️⃣ Testing COMPONENT-BASED scoring (Claude 3.5 Sonnet)...")
component_models = {
    'primary': 'anthropic/claude-3.5-sonnet',
    'fallbacks': ['openai/gpt-4-turbo']
}
try:
    result = scorer.score_job_component_based(job, profile, component_models, api_key)
    print(f"✅ Component: {result.get('final_score')}% using {result.get('model_used')}")
    print(f"   Components: {len(result.get('components', []))} extracted")
    print(f"   Recommendation: {result.get('recommendation')}")
except Exception as e:
    print(f"❌ Component failed: {e}")

# Test hireability
print(f"\n3️⃣ Testing HIREABILITY scoring (Claude 3.5 Sonnet)...")
hireability_models = {
    'primary': 'anthropic/claude-3.5-sonnet',
    'fallbacks': ['openai/gpt-4-turbo']
}
try:
    result = scorer.score_job_hireability_based(job, profile, hireability_models, api_key)
    score = result.get('score_breakdown', {}).get('final_score', 0)
    print(f"✅ Hireability: {score}% using {result.get('model_used')}")
    if result.get('hard_gate_failed'):
        print(f"   Hard gate failed: {result.get('hard_gate_failed')}")
    print(f"   Recommendation: {result.get('recommendation')}")
except Exception as e:
    print(f"❌ Hireability failed: {e}")

print(f"\n✅ Quick test complete!\n")
