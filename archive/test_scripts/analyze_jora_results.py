"""Quick analysis of Jora scraping results"""
import sys
sys.path.insert(0, 'src')
from database import get_all_jobs

# Get all Jora jobs
jobs = [j for j in get_all_jobs() if j.get('source') == 'jora']
print(f'\n🎯 JORA SCRAPER RESULTS')
print('=' * 60)
print(f'Total jobs scraped: {len(jobs)}')

# Score distribution
score_ranges = {'0-30%': 0, '31-50%': 0, '51-70%': 0, '71-85%': 0, '86-100%': 0}
for job in jobs:
    score = job.get('score', 0)
    if score <= 30:
        score_ranges['0-30%'] += 1
    elif score <= 50:
        score_ranges['31-50%'] += 1
    elif score <= 70:
        score_ranges['51-70%'] += 1
    elif score <= 85:
        score_ranges['71-85%'] += 1
    else:
        score_ranges['86-100%'] += 1

print('\n📊 Score Distribution:')
for range_name, count in score_ranges.items():
    pct = (count/len(jobs)*100) if jobs else 0
    print(f'  {range_name}: {count} jobs ({pct:.1f}%)')

# Top 10 jobs
print('\n🏆 Top 10 Matches:')
sorted_jobs = sorted(jobs, key=lambda x: x.get('score', 0), reverse=True)
for i, job in enumerate(sorted_jobs[:10], 1):
    print(f'  {i}. {job.get("score", 0)}% - {job["title"][:55]}')

# Description stats
desc_lengths = [len(j.get('description', '')) for j in jobs]
print(f'\n📝 Description Lengths:')
print(f'  Min: {min(desc_lengths):,} chars')
print(f'  Max: {max(desc_lengths):,} chars')
print(f'  Avg: {sum(desc_lengths)//len(desc_lengths):,} chars')
print('=' * 60)
