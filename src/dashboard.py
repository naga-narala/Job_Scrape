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


def build_filter_params():
    """Build filter query string from current request"""
    days = request.args.get('days', 7, type=int)
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    return f"days={days}&location={location}&region={region}"


def get_perth_now():
    """Get current datetime in Perth"""
    perth_tz = pytz.timezone('Australia/Perth')
    return datetime.now(perth_tz)


def group_jobs_by_status(jobs):
    """Group jobs by status"""
    status_order = [
        ('interested', '💚 Interested'),
        ('applied', '📤 Applied'),
        ('responded', '📧 Responded'),
        ('phone_screen', '📞 Phone Screen'),
        ('interview_scheduled', '🎯 Interview Scheduled'),
        ('interviewed', '💼 Interviewed'),
        ('follow_up', '🔄 Follow-up'),
        ('offer_received', '🎉 Offer Received'),
        ('new', '📋 New / To Review'),
        ('on_hold', '⏸️ On Hold'),
        ('accepted', '✅ Accepted'),
        ('declined_offer', '❌ Declined'),
        ('rejected', '🚫 Rejected')
    ]
    
    grouped = {label: [] for _, label in status_order}
    
    for job in jobs:
        status = job.get('status') or 'new'
        
        # Find the label for this status
        label = None
        for status_key, status_label in status_order:
            if status_key == status:
                label = status_label
                break
        
        if label and label in grouped:
            grouped[label].append(job)
    
    # Remove empty sections
    return {k: v for k, v in grouped.items() if v}


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
    """Main dashboard - last 30 days by default"""
    days = request.args.get('days', 30, type=int)
    location_filter = request.args.get('location', 'all')
    region_filter = request.args.get('region', 'all')
    
    config = load_config()
    hide_old_days = config.get('hide_jobs_older_than_days', 30)
    threshold = config.get('match_threshold', 0)  # Show all jobs (changed to 0)
    
    # Get jobs within date range (increased to 60 days to catch older jobs)
    jobs = db.get_jobs_by_date_range(days, hide_old_days=60)
    
    # Filter to exclude applied/rejected jobs only
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
    
    # Determine view mode
    view_mode = request.args.get('view', 'status')  # 'date' or 'status'
    
    # Group jobs
    if view_mode == 'status':
        jobs_by_status = group_jobs_by_status(jobs)
        jobs_by_date = {}
    else:
        jobs_by_date = group_jobs_by_date(jobs)
        jobs_by_status = {}
    
    # Calculate stats
    apply_count = sum(1 for j in jobs if j.get('recommendation') == 'APPLY')
    stats = {
        'total_matches': len(jobs),
        'apply_count': apply_count,
        'avg_score': round(sum(j.get('score', 0) for j in jobs) / len(jobs), 1) if jobs else 0,
        'last_updated': db.get_last_run_time()
    }
    
    # Get today's date formatted nicely
    today_date = get_perth_now().strftime("%B %d, %Y")
    
    return render_template(
        'dashboard_hybrid.html',
        jobs_by_date=jobs_by_date,
        jobs_by_status=jobs_by_status,
        stats=stats,
        today_date=today_date,
        current_days=days,
        threshold=threshold,
        show_all=False,
        location_filter=location_filter,
        region_filter=region_filter,
        view_mode=view_mode,
        current_path=request.path,
        filter_params=build_filter_params()
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
    
    apply_count = sum(1 for j in jobs if j.get('recommendation') == 'APPLY')
    stats = {
        'total_matches': len(jobs),
        'apply_count': apply_count,
        'avg_score': round(sum(j.get('score', 0) for j in jobs) / len(jobs), 1) if jobs else 0,
        'last_updated': db.get_last_run_time()
    }
    
    today_date = get_perth_now().strftime("%B %d, %Y")
    
    return render_template(
        'dashboard_hybrid.html',
        jobs_by_date=jobs_by_date,
        stats=stats,
        today_date=today_date,
        current_days=999,
        threshold=threshold,
        show_all=True,
        location_filter=location_filter,
        region_filter=region_filter,
        current_path=request.path,
        filter_params=build_filter_params()
    )


@app.route('/stats')
def stats():
    """Statistics page"""
    location_filter = request.args.get('location', 'all')
    region_filter = request.args.get('region', 'all')
    
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
    
    return render_template(
        'stats.html',
        stats=stats_data,
        location_filter=location_filter,
        region_filter=region_filter,
        current_path=request.path,
        filter_params=build_filter_params()
    )


@app.route('/applied')
def applied_jobs():
    """Show jobs marked as applied with timeline tracking"""
    status_filter = request.args.get('status', 'all')
    location_filter = request.args.get('location', 'all')
    region_filter = request.args.get('region', 'all')
    
    jobs = db.get_applied_jobs()
    
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
    
    # Filter by status if specified
    if status_filter != 'all':
        jobs = [j for j in jobs if j.get('status') == status_filter]
    
    return render_template(
        'applied.html',
        jobs=jobs,
        status_filter=status_filter,
        location_filter=location_filter,
        region_filter=region_filter,
        current_path=request.path,
        filter_params=build_filter_params()
    )


@app.route('/rejected')
def rejected_jobs():
    """Show rejected jobs with rejection reasons"""
    location_filter = request.args.get('location', 'all')
    region_filter = request.args.get('region', 'all')
    
    jobs = db.get_rejected_jobs()
    
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
    
    return render_template(
        'rejected.html',
        jobs=jobs,
        location_filter=location_filter,
        region_filter=region_filter,
        current_path=request.path,
        filter_params=build_filter_params()
    )


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """Detailed job view with full hybrid scoring breakdown"""
    job = db.get_job(job_id)
    if not job:
        return "Job not found", 404
    
    # Get score details
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*
        FROM scores s
        WHERE s.job_id = ?
    ''', (job_id,))
    
    score_row = cursor.fetchone()
    conn.close()
    
    if score_row:
        score = dict(score_row)
        # Parse hybrid fields
        score = db._parse_job_hybrid_fields(score)
        job.update(score)
    
    return render_template('job_detail.html', job=job)


@app.route('/api/job/<int:job_id>/components')
def job_components_api(job_id):
    """API endpoint for job components (AJAX)"""
    job = db.get_job(job_id)
    if not job:
        return {"error": "Job not found"}, 404
    
    # Get hybrid scoring details
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.components, s.hireability_factors, s.risk_profile, s.score_breakdown
        FROM scores s
        WHERE s.job_id = ?
    ''', (job_id,))
    
    score_row = cursor.fetchone()
    conn.close()
    
    if score_row:
        score = dict(score_row)
        score = db._parse_job_hybrid_fields(score)
        return score
    
    return {"error": "No score found"}, 404


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
    """Manually rescore a single job using hybrid scoring"""
    try:
        job = db.get_job(job_id)
        if not job:
            return "Job not found", 404
        
        config = load_config()
        profile = scorer.load_profile()
        
        # Score the job with hybrid system
        models_config = config.get('ai', {}).get('models', {})
        score_result = scorer.score_job_with_fallback(
            job,
            profile,
            models_config,
            config.get('openrouter_api_key')
        )
        
        # Update score
        profile_hash = db.get_profile_hash()
        db.delete_score(job_id)
        db.insert_score(job_id, score_result, profile_hash)
        
        return redirect(request.referrer or url_for('index'))
        
    except Exception as e:
        return f"Error rescoring job: {e}", 500


### ===================================================================
### APPLICATION TRACKING SYSTEM (ATS) ROUTES
### ===================================================================

@app.route('/job/<int:job_id>/status', methods=['POST'])
def update_job_status_route(job_id):
    """Update job status with history tracking"""
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    try:
        db.update_job_status_with_history(job_id, new_status, notes)
        return redirect(request.referrer or url_for('index'))
    except Exception as e:
        return f"Error updating status: {e}", 500


@app.route('/job/<int:job_id>/status-history')
def job_status_history(job_id):
    """Get status history for a job (JSON API)"""
    try:
        history = db.get_status_history(job_id)
        return {'status': 'success', 'history': history}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


@app.route('/status/<status>')
def jobs_by_status(status):
    """View jobs filtered by status"""
    jobs = db.get_jobs_by_status_filter(status)
    
    status_names = {
        'new': 'New Jobs',
        'interested': 'Interested',
        'applied': 'Applied',
        'responded': 'Responded',
        'phone_screen': 'Phone Screen',
        'interview_scheduled': 'Interview Scheduled',
        'interviewed': 'Interviewed',
        'follow_up': 'Follow-up',
        'offer_received': 'Offer Received',
        'accepted': 'Accepted',
        'declined_offer': 'Declined Offer',
        'rejected': 'Rejected',
        'on_hold': 'On Hold'
    }
    
    # Get Perth time for today's date
    today_date = get_perth_now().strftime("%B %d, %Y")
    
    # Calculate stats
    stats = {
        'total_matches': len(jobs),
        'apply_count': sum(1 for j in jobs if j.get('recommendation') == 'APPLY'),
        'avg_score': round(sum(j.get('score', 0) for j in jobs) / len(jobs), 1) if jobs else 0,
        'last_updated': db.get_last_run_time()
    }
    
    return render_template(
        'dashboard_hybrid.html',
        jobs_by_date=group_jobs_by_date(jobs),
        stats=stats,
        today_date=today_date,
        current_days=999,
        threshold=0,
        show_all=True,
        location_filter='all',
        region_filter='all',
        current_status=status,
        status_name=status_names.get(status, status.title()),
        current_path=request.path,
        filter_params=build_filter_params()
    )


@app.route('/job/<int:job_id>/interview', methods=['POST'])
def schedule_interview(job_id):
    """Schedule interview for job"""
    interview_data = {
        'interview_date': request.form.get('interview_date'),
        'interview_type': request.form.get('interview_type'),
        'interviewer_name': request.form.get('interviewer_name', ''),
        'topics_discussed': request.form.get('topics_discussed', ''),
        'questions_asked': request.form.get('questions_asked', ''),
        'my_performance': request.form.get('my_performance', ''),
        'next_steps': request.form.get('next_steps', ''),
        'notes': request.form.get('notes', '')
    }
    
    try:
        db.add_interview(job_id, interview_data)
        # Update status to interview_scheduled if not already
        db.update_job_status_with_history(job_id, 'interview_scheduled', 'Interview scheduled')
        return redirect(request.referrer or url_for('job_detail', job_id=job_id))
    except Exception as e:
        return f"Error scheduling interview: {e}", 500


@app.route('/job/<int:job_id>/interviews')
def job_interviews(job_id):
    """Get interviews for a job (JSON API)"""
    try:
        interviews = db.get_interviews_for_job(job_id)
        return {'status': 'success', 'interviews': interviews}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


@app.route('/interviews/upcoming')
def upcoming_interviews():
    """View upcoming interviews"""
    days = request.args.get('days', 30, type=int)
    interviews = db.get_upcoming_interviews(days)
    
    today_date = get_perth_now().strftime("%B %d, %Y")
    
    return render_template(
        'interviews.html',
        interviews=interviews,
        today_date=today_date,
        days=days
    )


@app.route('/job/<int:job_id>/priority', methods=['POST'])
def set_priority(job_id):
    """Set job priority"""
    priority = request.form.get('priority', 0, type=int)
    
    try:
        db.set_job_priority(job_id, priority)
        return redirect(request.referrer or url_for('index'))
    except Exception as e:
        return f"Error setting priority: {e}", 500


@app.route('/job/<int:job_id>/note', methods=['POST'])
def add_note(job_id):
    """Add note to job"""
    note = request.form.get('note', '')
    
    try:
        db.add_job_note(job_id, note)
        return redirect(request.referrer or url_for('job_detail', job_id=job_id))
    except Exception as e:
        return f"Error adding note: {e}", 500


@app.route('/analytics')
def analytics():
    """Analytics dashboard with status funnel"""
    status_stats = db.get_status_statistics()
    
    today_date = get_perth_now().strftime("%B %d, %Y")
    
    return render_template(
        'analytics.html',
        status_stats=status_stats,
        today_date=today_date
    )


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
