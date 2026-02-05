import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import logging
import os
import webbrowser
from pathlib import Path
import pytz

logger = logging.getLogger(__name__)


def get_perth_datetime():
    """Get current datetime in Perth timezone formatted"""
    perth_tz = pytz.timezone('Australia/Perth')
    return datetime.now(perth_tz).strftime('%Y-%m-%d_%H-%M-%S')


def get_perth_date_formatted():
    """Get current date in Perth timezone formatted nicely"""
    perth_tz = pytz.timezone('Australia/Perth')
    return datetime.now(perth_tz).strftime('%b %d, %Y')


def build_email_html(jobs, date_str):
    """Build dynamic HTML content with structured match analysis"""
    
    # Sort jobs by score
    jobs_sorted = sorted(jobs, key=lambda x: x.get('score', 0), reverse=True)
    
    # Build job cards HTML
    job_cards_html = ""
    for job in jobs_sorted:
        score = job.get('score', 0)
        
        # Determine score styling
        if score >= 90:
            score_color = '#10b981'
            score_bg = '#d1fae5'
        elif score >= 80:
            score_color = '#f59e0b'
            score_bg = '#fef3c7'
        elif score >= 70:
            score_color = '#3b82f6'
            score_bg = '#dbeafe'
        else:
            score_color = '#6b7280'
            score_bg = '#f3f4f6'
        
        # Build matched items checklist
        matched_items = job.get('matched', [])
        matched_html = ""
        if matched_items:
            for item in matched_items:
                matched_html += f'<li style="color: #059669; margin: 8px 0;"><span style="color: #10b981; font-weight: bold;">✓</span> {item}</li>'
        
        # Build not matched items checklist
        not_matched_items = job.get('not_matched', [])
        not_matched_html = ""
        if not_matched_items:
            for item in not_matched_items:
                not_matched_html += f'<li style="color: #dc2626; margin: 8px 0;"><span style="color: #ef4444; font-weight: bold;">✗</span> {item}</li>'
        
        # Build key points
        key_points = job.get('key_points', [])
        key_points_html = ""
        if key_points:
            for point in key_points:
                key_points_html += f'<li style="color: #4b5563; margin: 8px 0;"><span style="color: #3b82f6;">💡</span> {point}</li>'
        
        # Fallback to old format if new format not available
        if not matched_html and not not_matched_html and not key_points_html:
            reasoning = job.get('reasoning', 'No analysis provided')
            key_points_html = f'<li style="color: #4b5563; margin: 8px 0;"><span style="color: #3b82f6;">💡</span> {reasoning}</li>'
        
        job_cards_html += f'''
        <div style="border: 1px solid #e5e7eb; padding: 24px; margin: 20px 0; border-radius: 12px; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 8px 0; color: #111827; font-size: 18px;">
                        <a href="{job.get('url', '#')}" style="color: #0066cc; text-decoration: none;">{job.get('title', 'Unknown')}</a>
                    </h3>
                    <p style="margin: 0; color: #6b7280; font-size: 14px;">
                        <strong style="color: #374151;">{job.get('company', 'Unknown')}</strong> · {job.get('location', 'Unknown')}
                    </p>
                </div>
                <div style="background: {score_bg}; color: {score_color}; padding: 12px 20px; border-radius: 8px; font-size: 24px; font-weight: bold; min-width: 80px; text-align: center;">
                    {score}%
                </div>
            </div>
            
            <!-- Analysis Sections -->
            <div style="margin-top: 20px;">
                {f'<div style="margin-bottom: 16px;"><h4 style="color: #059669; margin: 0 0 8px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">✓ What Matches</h4><ul style="margin: 0; padding-left: 20px;">{matched_html}</ul></div>' if matched_html else ''}
                
                {f'<div style="margin-bottom: 16px;"><h4 style="color: #dc2626; margin: 0 0 8px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">✗ Concerns</h4><ul style="margin: 0; padding-left: 20px;">{not_matched_html}</ul></div>' if not_matched_html else ''}
                
                {f'<div><h4 style="color: #3b82f6; margin: 0 0 8px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">💡 Key Points</h4><ul style="margin: 0; padding-left: 20px;">{key_points_html}</ul></div>' if key_points_html else ''}
            </div>
            
            <!-- Actions -->
            <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                <a href="{job.get('url', '#')}" style="background: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: 500;">
                    View on LinkedIn →
                </a>
                <span style="margin-left: 16px; color: #9ca3af; font-size: 13px;">Posted: {job.get('first_seen_date', 'Unknown')}</span>
            </div>
        </div>
        '''
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                max-width: 700px; 
                margin: 0 auto; 
                padding: 20px;
                background: #f9fafb;
            }}
            h2 {{ 
                color: #111827;
                font-size: 28px;
                margin-bottom: 8px;
            }}
            .subtitle {{
                color: #6b7280;
                font-size: 16px;
                margin-top: 0;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #e5e7eb;
                color: #6b7280;
                font-size: 14px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h2>🎯 {len(jobs)} New Job Match{'es' if len(jobs) != 1 else ''}</h2>
        <p class="subtitle">Found {len(jobs)} new opportunity{'ies' if len(jobs) != 1 else 'y'} matching your profile · {date_str}</p>
        
        {job_cards_html}
        
        <div class="footer">
            <p style="margin-bottom: 8px;"><a href="http://localhost:5000" style="color: #0066cc; text-decoration: none;">📊 View Full Dashboard</a></p>
            <p style="margin: 0;">Automated notification from Job Scraper</p>
        </div>
    </body>
    </html>
    '''
    
    return html


def send_email_notification(jobs, config):
    """
    Send email notification via SMTP
    Returns: True if successful, False otherwise
    """
    try:
        smtp_host = config.get('email_smtp_host', 'smtp.gmail.com')
        smtp_port = config.get('email_smtp_port', 587)
        from_email = config.get('email_from')
        password = config.get('email_password')
        to_email = config.get('email_to')
        
        if not all([from_email, password, to_email]):
            logger.error("Email configuration incomplete")
            return False
        
        date_str = get_perth_date_formatted()
        subject = f"{len(jobs)} New Job Match{'es' if len(jobs) != 1 else ''} ({date_str})"
        
        html_content = build_email_html(jobs, date_str)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Try sending with retries
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempting to send email (attempt {attempt}/{max_retries})...")
                
                with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(from_email, password)
                    server.send_message(msg)
                
                logger.info(f"✓ Email sent successfully to {to_email}")
                return True
                
            except smtplib.SMTPAuthenticationError:
                logger.error("SMTP authentication failed. Check email/password.")
                return False
                
            except Exception as e:
                logger.warning(f"Email attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(60)  # Wait 1 minute before retry
                else:
                    logger.error(f"All {max_retries} email attempts failed")
                    return False
        
        return False
        
    except Exception as e:
        logger.error(f"Email notification error: {e}")
        return False


def save_html_notification(jobs):
    """
    Save notification as HTML file and auto-open in browser
    Returns: filepath if successful
    """
    try:
        notifications_dir = Path(__file__).parent.parent / 'data' / 'notifications'
        notifications_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = get_perth_datetime()
        filename = f"job_matches_{timestamp}.html"
        filepath = notifications_dir / filename
        
        date_str = get_perth_date_formatted()
        html_content = build_email_html(jobs, date_str)
        
        # Add extra header for file viewing
        html_with_header = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Job Matches - {date_str}</title>
        </head>
        <body>
        {html_content}
        </body>
        </html>
        '''
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_with_header)
        
        logger.info(f"HTML notification saved: {filepath}")
        
        # Auto-open in browser
        try:
            webbrowser.open(f'file://{filepath.absolute()}')
            logger.info("HTML notification opened in browser")
        except Exception as e:
            logger.warning(f"Could not auto-open browser: {e}")
        
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Failed to save HTML notification: {e}")
        return None


def notify_new_matches(config):
    """
    Send notifications for new high-scoring jobs
    Tries email first, falls back to HTML file
    Returns: dict with notification stats
    """
    import database as db
    
    threshold = config.get('match_threshold', 75)
    jobs = db.get_high_scoring_unnotified(threshold)
    
    if not jobs:
        logger.info("No new matches to notify")
        return {'notified': 0, 'method': None, 'success': True}
    
    logger.info(f"Notifying {len(jobs)} new match{'es' if len(jobs) != 1 else ''}")
    
    # Try email first
    email_success = send_email_notification(jobs, config)
    
    if email_success:
        # Mark all as notified via email
        for job in jobs:
            db.mark_notified(job['id'], 'email', 'success')
        
        return {
            'notified': len(jobs),
            'method': 'email',
            'success': True
        }
    else:
        # Email failed, use HTML fallback
        logger.warning("Email failed, using HTML fallback notification")
        
        html_path = save_html_notification(jobs)
        
        if html_path:
            # Mark as notified via HTML
            for job in jobs:
                db.mark_notified(job['id'], 'html', 'fallback')
            
            return {
                'notified': len(jobs),
                'method': 'html',
                'success': True,
                'file': html_path
            }
        else:
            # Both methods failed
            logger.error("Both email and HTML notifications failed")
            return {
                'notified': 0,
                'method': None,
                'success': False
            }
