#!/usr/bin/env python3
import sys
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import pytz

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

import database as db
import scorer
import rescore_manager
import json

app = Flask(__name__, template_folder=str(Path(__file__).parent.parent / 'templates'))


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def get_perth_now():
    """Get current datetime in Perth"""
    perth_tz = pytz.timezone('Australia/Perth')
    return datetime.now(perth_tz)


def group_jobs_by_date(jobs):
    """Group jobs by relative date labels"""
    now = get_perth_now().date()
    grouped = {}
    
    for job in jobs:
        # Parse first_seen_date
        if isinstance(job['first_seen_date'], str):
            job_date = datetime.fromisoformat(job['first_seen_date']).date()
        else:
            job_date = job['first_seen_date']
        
        days_ago = (now - job_date).days
        
        # Determine label
        if days_ago == 0:
            label = "Today"
        elif days_ago == 1:
            label = "Yesterday"
        elif days_ago <= 7:
            label = f"{days_ago} days ago"
        elif days_ago <= 30:
            label = job_date.strftime("%b %d, %Y")
        else:
            label = job_date.strftime("%b %Y")
        
        if label not in grouped:
            grouped[label] = []
        
        # Add score class for CSS styling
        score = job.get('score', 0)
        if score >= 90:
            job['score_class'] = '90'
        elif score >= 80:
            job['score_class'] = '80'
        else:
            job['score_class'] = '75'
        
        grouped[label].append(job)
    
    return grouped


@app.route('/')
def index():
    """Main dashboard - last 7 days by default"""
    days = request.args.get('days', 7, type=int)
    location_filter = request.args.get('location', 'all')
    region_filter = request.args.get('region', 'all')
    
    config = load_config()
    hide_old_days = config.get('hide_jobs_older_than_days', 30)
    threshold = config.get('match_threshold', 30)  # Show jobs ≥threshold
    
    # Get jobs within date range
    jobs = db.get_jobs_by_date_range(days, hide_old_days)
    
    # Filter to only high-scoring jobs (≥50%) and exclude applied/rejected jobs
    jobs = [j for j in jobs if j.get('score', 0) >= threshold and not j.get('applied', 0) and not j.get('rejected', 0)]
    
    # Apply region filter
    if region_filter == 'australia':
        jobs = [j for j in jobs if j.get('region', 'australia') == 'australia']
    elif region_filter == 'us':
        jobs = [j for j in jobs if j.get('region', 'australia') == 'us']
    
    # Apply location filter
    if location_filter == 'perth':
        # Perth - any work type (remote/hybrid/onsite)
        jobs = [j for j in jobs if j.get('location') and 'perth' in j['location'].lower()]
    elif location_filter == 'australia':
        # Anywhere in Australia - remote or hybrid only
        jobs = [j for j in jobs if j.get('location') and 
                ('australia' in j['location'].lower() or any(city in j['location'].lower() 
                 for city in ['sydney', 'melbourne', 'perth', 'brisbane', 'adelaide', 'canberra'])) and
                ('remote' in j['location'].lower() or 'hybrid' in j['location'].lower())]
    elif location_filter == 'world':
        # Anywhere in world - remote only
        jobs = [j for j in jobs if j.get('location') and 'remote' in j['location'].lower()]
    
    # Group by date
    jobs_by_date = group_jobs_by_date(jobs)
    
    # Calculate stats
    stats = {
        'total_matches': len(jobs),
        'avg_score': round(sum(j.get('score', 0) for j in jobs) / len(jobs), 1) if jobs else 0,
        'last_updated': db.get_last_run_time()
    }
    
    return render_template(
        'dashboard.html',
        jobs_by_date=jobs_by_date,
        stats=stats,
        current_days=days,
        threshold=threshold,
        show_all=False,
        location_filter=location_filter,
        region_filter=region_filter
    )


@app.route('/all')
def show_all():
    """Show all jobs regardless of age"""
    location_filter = request.args.get('location', 'all')
    region_filter = request.args.get('region', 'all')
    
    config = load_config()
    threshold = config.get('match_threshold', 30)
    
    jobs = db.get_all_jobs(include_inactive=False)
    
    # Filter to high-scoring and exclude applied/rejected jobs
    jobs = [j for j in jobs if j.get('score', 0) >= threshold and not j.get('applied', 0) and not j.get('rejected', 0)]
    
    # Apply region filter
    if region_filter == 'australia':
        jobs = [j for j in jobs if j.get('region', 'australia') == 'australia']
    elif region_filter == 'us':
        jobs = [j for j in jobs if j.get('region', 'australia') == 'us']
    
    # Apply location filter
    if location_filter == 'perth':
        jobs = [j for j in jobs if j.get('location') and 'perth' in j['location'].lower()]
    elif location_filter == 'australia':
        jobs = [j for j in jobs if j.get('location') and 
                ('australia' in j['location'].lower() or any(city in j['location'].lower() 
                 for city in ['sydney', 'melbourne', 'perth', 'brisbane', 'adelaide', 'canberra'])) and
                ('remote' in j['location'].lower() or 'hybrid' in j['location'].lower())]
    elif location_filter == 'world':
        jobs = [j for j in jobs if j.get('location') and 'remote' in j['location'].lower()]
    
    jobs_by_date = group_jobs_by_date(jobs)
    
    stats = {
        'total_matches': len(jobs),
        'avg_score': round(sum(j.get('score', 0) for j in jobs) / len(jobs), 1) if jobs else 0,
        'last_updated': db.get_last_run_time()
    }
    
    return render_template(
        'dashboard.html',
        jobs_by_date=jobs_by_date,
        stats=stats,
        current_days=999,
        threshold=threshold,
        show_all=True,
        location_filter=location_filter,
        region_filter=region_filter
    )


@app.route('/stats')
def stats():
    """Statistics page"""
    config = load_config()
    threshold = config.get('match_threshold', 30)
    
    stats_data = {
        'total_jobs': db.count_all_jobs(),
        'total_matches': db.count_jobs_above_threshold(threshold),
        'avg_score': db.get_average_score(),
        'top_companies': db.get_top_companies(10),
        'score_distribution': db.get_score_distribution(),
        'threshold': threshold
    }
    
    return render_template('stats.html', stats=stats_data)


@app.route('/applied')
def applied_jobs():
    """Show jobs marked as applied with timeline tracking"""
    status_filter = request.args.get('status', 'all')
    
    jobs = db.get_applied_jobs()
    
    # Filter by status if specified
    if status_filter != 'all':
        jobs = [j for j in jobs if j.get('status') == status_filter]
    
    return render_template(
        'applied.html',
        jobs=jobs,
        status_filter=status_filter
    )


@app.route('/rejected')
def rejected_jobs():
    """Show rejected jobs with rejection reasons"""
    jobs = db.get_rejected_jobs()
    
    return render_template(
        'rejected.html',
        jobs=jobs
    )


@app.route('/apply/<int:job_id>', methods=['POST'])
def mark_applied(job_id):
    """Mark job as applied"""
    db.mark_applied(job_id)
    return redirect(request.referrer or url_for('index'))


@app.route('/update-status/<int:job_id>', methods=['POST'])
def update_status(job_id):
    """Update job application status"""
    status = request.form.get('status')
    remarks = request.form.get('remarks')
    db.update_job_status(job_id, status, remarks)
    return redirect(request.referrer or url_for('applied_jobs'))


@app.route('/reject/<int:job_id>', methods=['POST'])
def reject_job_route(job_id):
    """Mark job as rejected with feedback"""
    category = request.form.get('rejection_category')
    notes = request.form.get('rejection_notes', '')
    
    if not category:
        return "Rejection category required", 400
    
    success = db.reject_job(job_id, category, notes)
    
    if not success:
        return "Failed to reject job", 500
    
    return redirect(request.referrer or url_for('index'))


@app.route('/rescore/<int:job_id>', methods=['POST'])
def rescore_job(job_id):
    """Manually rescore a single job"""
    try:
        job = db.get_job(job_id)
        if not job:
            return "Job not found", 404
        
        config = load_config()
        profile = scorer.load_profile()
        
        # Score the job
        score_result = scorer.score_job_with_fallback(
            job,
            profile,
            config.get('ai_models', {}),
            config.get('openrouter_api_key')
        )
        
        # Update score
        profile_hash = db.get_profile_hash()
        db.delete_score(job_id)
        db.insert_score(job_id, score_result, profile_hash)
        
        return redirect(request.referrer or url_for('index'))
        
    except Exception as e:
        return f"Error rescoring job: {e}", 500


if __name__ == "__main__":
    # Initialize database
    db.init_database()
    
    import os
    port = int(os.environ.get('PORT', 8000))
    
    print("=" * 70)
    print("Job Scraper Dashboard")
    print("=" * 70)
    print(f"Dashboard running at: http://localhost:{port}")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=port, debug=False)
