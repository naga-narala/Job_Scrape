#!/usr/bin/env python3
"""
TIER 1 FILTERED JOBS - COMPLETE LIST
Extracted from workflow execution logs
"""

print("=" * 80)
print("🚫 TIER 1 FILTERED JOBS (By Title)")
print("=" * 80)

page1_filtered = [
    ("Engineering Manager- AI Developer Tooling Workflows (Remote ANZ)", "Title contains senior/leadership keyword: manager"),
    ("Senior Machine Learning Engineer", "Title contains senior/leadership keyword: senior"),
    ("AI Engineering Lead - Build, Shape, and Lead Next-Gen AI Platforms", "Title contains senior/leadership keyword: lead"),
    ("Data Engineer (SSE / Staff Engineer) - Python & Spark & AWS", "Title contains senior/leadership keyword: staff"),
    ("Data Scientist | LLM Engineer | Senior Associate/Manager", "Title contains senior/leadership keyword: senior"),
    ("Member of Technical Staff - Knowledge Graph", "Title contains senior/leadership keyword: staff"),
    ("Senior Engineer - Data and Business Intelligence", "Title contains senior/leadership keyword: senior"),
    ("Principal BI Developer", "Title contains senior/leadership keyword: principal"),
]

page2_filtered = [
    ("Senior Machine Learning Engineer - AI Data Trainer", "Title contains senior/leadership keyword: senior"),
    ("Engineering Manager- AI Developer Tooling Workflows (Remote ANZ)", "Title contains senior/leadership keyword: manager"),
    ("Lead Data Engineer", "Title contains senior/leadership keyword: lead"),
    ("Staff Infrastructure Security Engineer", "Title contains senior/leadership keyword: staff"),
    ("Senior React Developer", "Title contains senior/leadership keyword: senior"),
    ("Senior Cloud & DevOps Engineer (NV1 cleared)", "Title contains senior/leadership keyword: senior"),
    ("Senior Software Developer", "Title contains senior/leadership keyword: senior"),
    ("Senior Data Engineer", "Title contains senior/leadership keyword: senior"),
    ("Engineer-Senior I", "Title contains senior/leadership keyword: senior"),
    ("Cloud Platform Principal Engineer - AWS", "Title contains senior/leadership keyword: principal"),
]

page3_filtered = [
    ("Senior Machine Learning Engineer - AI Data Trainer", "Title contains senior/leadership keyword: senior"),
    ("Senior Backend Engineer - (Java) - Teams & Education", "Title contains senior/leadership keyword: senior"),
    ("Senior Frontend Engineer (Australia - AEST, Remote)", "Title contains senior/leadership keyword: senior"),
    ("Staff Software Engineer, Backend", "Title contains senior/leadership keyword: staff"),
    ("Senior Software Engineer", "Title contains senior/leadership keyword: senior"),
    ("Senior AWS Data Engineer", "Title contains senior/leadership keyword: senior"),
]

print("\n📄 PAGE 1 - 8 Jobs Filtered:")
print("-" * 80)
for i, (title, reason) in enumerate(page1_filtered, 1):
    print(f"\n{i}. {title}")
    print(f"   ❌ Reason: {reason}")

print("\n\n📄 PAGE 2 - 10 Jobs Filtered:")
print("-" * 80)
for i, (title, reason) in enumerate(page2_filtered, 1):
    print(f"\n{i}. {title}")
    print(f"   ❌ Reason: {reason}")

print("\n\n📄 PAGE 3 - 6 Jobs Filtered:")
print("-" * 80)
for i, (title, reason) in enumerate(page3_filtered, 1):
    print(f"\n{i}. {title}")
    print(f"   ❌ Reason: {reason}")

print("\n" + "=" * 80)
print("📊 FILTERING SUMMARY")
print("=" * 80)

# Count filtering reasons
all_filtered = page1_filtered + page2_filtered + page3_filtered
reason_counts = {}
for title, reason in all_filtered:
    if 'senior' in reason.lower():
        key = 'Senior/Leadership roles'
    elif 'staff' in reason.lower():
        key = 'Staff roles'
    elif 'principal' in reason.lower():
        key = 'Principal roles'
    elif 'lead' in reason.lower():
        key = 'Lead roles'
    elif 'manager' in reason.lower():
        key = 'Manager roles'
    else:
        key = 'Other'
    
    reason_counts[key] = reason_counts.get(key, 0) + 1

print(f"\nTotal filtered: {len(all_filtered)} jobs across 3 pages")
print(f"  • Page 1: 8 jobs")
print(f"  • Page 2: 10 jobs")
print(f"  • Page 3: 6 jobs")

print(f"\n🎯 Filtering Breakdown:")
for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  • {reason}: {count} jobs")

print("\n💡 Why These Were Filtered:")
print("  Tier 1 filtering removes senior/leadership positions because:")
print("  • You're searching for 'Graduate' and entry-level roles")
print("  • Senior roles typically require 5+ years of experience")
print("  • This prevents wasting time scraping irrelevant job details")
print("  • Saves API calls and speeds up the overall workflow")

print("\n" + "=" * 80)
