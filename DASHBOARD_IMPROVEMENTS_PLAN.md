# Dashboard Improvements Plan
**Date:** February 15, 2026

## Overview
Two major enhancements to make the dashboard a complete Application Tracking System (ATS):
1. **Advanced Date Filtering** - Intuitive, visual date range selection
2. **Application Tracking System** - Full lifecycle tracking from discovery to outcome

---

## Part 1: Advanced Date Filtering System

### Current State
- Basic date filter (last 7, 14, 30 days)
- Hidden in dropdowns
- Not intuitive

### Proposed Design

#### Visual Date Filter Bar (Horizontal Tabs + Custom Range)

```
┌─────────────────────────────────────────────────────────────┐
│ 📅 DATE RANGE:                                              │
│ [Today] [This Week] [This Month] [Last 7 Days] [Custom ▾]  │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
1. **Quick Filters** (Always visible chips):
   - Today (1 day)
   - This Week (7 days)
   - This Month (30 days)
   - Last 90 Days
   - All Time

2. **Custom Date Range** (Expandable):
   ```
   From: [📅 MM/DD/YYYY] To: [📅 MM/DD/YYYY] [Apply]
   ```

3. **Visual Timeline** (Show job distribution):
   ```
   Today     ████░░░░░░ 12 jobs
   Yesterday ██████████ 25 jobs
   This Week ████████░░ 45 jobs
   Older     ██░░░░░░░░ 8 jobs
   ```

#### Design Specs
```css
.date-filter-bar {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
}

.date-chip {
    padding: 8px 16px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
}

.date-chip.active {
    background: #2563eb;
    color: white;
    border-color: #2563eb;
}

.date-chip:hover:not(.active) {
    background: #f1f5f9;
    border-color: #94a3b8;
}
```

---

## Part 2: Application Tracking System (ATS)

### Job Status Lifecycle

```
Discovery → Interested → Applied → Interview → Offer → Accepted/Rejected
```

#### Complete Status Flow

```
📋 NEW (default)
  ↓
💚 INTERESTED (bookmarked for later)
  ↓
📤 APPLIED (application submitted)
  ↓
📧 RESPONDED (employer contacted back)
  ↓
📞 PHONE SCREEN (initial call scheduled/completed)
  ↓
🎯 INTERVIEW SCHEDULED (interview date set)
  ↓
💼 INTERVIEWED (interview completed)
  ↓
🔄 FOLLOW-UP (waiting for response/additional rounds)
  ↓
🎉 OFFER RECEIVED (got job offer)
  ↓
✅ ACCEPTED (took the job) 
❌ DECLINED OFFER (rejected offer)
🚫 REJECTED (employer rejected)
⏸️  ON HOLD (paused/deferred)
```

### Database Schema Updates

#### Extend `jobs` table:
```sql
ALTER TABLE jobs ADD COLUMN interview_date DATE;
ALTER TABLE jobs ADD COLUMN interview_type TEXT;  -- phone, video, onsite, panel
ALTER TABLE jobs ADD COLUMN offer_date DATE;
ALTER TABLE jobs ADD COLUMN offer_amount REAL;
ALTER TABLE jobs ADD COLUMN offer_currency TEXT DEFAULT 'AUD';
ALTER TABLE jobs ADD COLUMN decision_date DATE;
ALTER TABLE jobs ADD COLUMN follow_up_date DATE;
ALTER TABLE jobs ADD COLUMN priority INTEGER DEFAULT 0;  -- 0=normal, 1=high, 2=urgent
ALTER TABLE jobs ADD COLUMN notes TEXT;  -- General notes
```

#### New `status_history` table:
```sql
CREATE TABLE status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);
```

#### New `interview_notes` table:
```sql
CREATE TABLE interview_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    interview_date DATE NOT NULL,
    interview_type TEXT,  -- phone, video, onsite, panel
    interviewer_name TEXT,
    topics_discussed TEXT,
    questions_asked TEXT,
    my_performance TEXT,  -- great, good, okay, poor
    next_steps TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);
```

---

## Dashboard UI Design

### Main View: Kanban Board Style

```
┌─────────────────────────────────────────────────────────────────────┐
│ VIEW MODE: [📋 List] [📊 Kanban] [📈 Pipeline]                      │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┬──────────────┬─────────┐
│ 💚 INTERESTED│ 📤 APPLIED   │ 📞 INTERVIEW │ 🎉 OFFER     │ ✅ DONE │
│     (23)     │     (15)     │     (8)      │     (2)      │   (45)  │
├──────────────┼──────────────┼──────────────┼──────────────┼─────────┤
│ AI Engineer  │ ML Engineer  │ Data Sci     │ AI Consult   │ Rejected│
│ @ Atlassian  │ @ Canva      │ @ CommBank   │ @ Deloitte   │   (30)  │
│ 96% • Today  │ 92% • 2d ago │ 88% • 1w ago │ 95% • 3d ago │ Accepted│
│ [Details ▾]  │ Next: Call   │ Mon 9AM      │ $140k AUD    │   (15)  │
│              │ [Track ⚡]   │ [Prep 📝]    │ [Decide 💭]  │         │
├──────────────┼──────────────┼──────────────┼──────────────┼─────────┤
│ Data Eng...  │ ...          │ ...          │              │         │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────┘
```

### List View with Status Badges

```
┌─────────────────────────────────────────────────────────────────────┐
│ FILTERS: [Status ▾] [Date ▾] [Score ▾] [Platform ▾]                │
├─────────────────────────────────────────────────────────────────────┤
│ 📤 APPLIED • 96% • AI Engineer @ Atlassian                          │
│ Applied: Feb 10 • Next: Phone Screen on Feb 17                      │
│ WHY APPLY: ✓ Python ✓ LLMs ✓ Visa OK                               │
│ [View Job] [Update Status] [Add Note] [Schedule Interview]         │
├─────────────────────────────────────────────────────────────────────┤
│ 🎯 INTERVIEW • 92% • ML Engineer @ Canva                            │
│ Interview: Feb 16 10:00 AM (Video) • Interviewer: Sarah Chen       │
│ WHY APPLY: ✓ ML ✓ PyTorch ✓ Remote                                 │
│ [View Job] [Interview Prep] [Add Notes] [Reschedule]               │
└─────────────────────────────────────────────────────────────────────┘
```

### Job Detail Modal (Expanded)

```
┌─────────────────────────────────────────────────────────────────────┐
│ AI Engineer @ Atlassian                              [X] Close      │
├─────────────────────────────────────────────────────────────────────┤
│ STATUS: 📤 Applied                                                  │
│ SCORE: 96% (APPLY)     MATCH: Excellent     RISK: Low              │
├─────────────────────────────────────────────────────────────────────┤
│ ⏱️  TIMELINE:                                                        │
│ • Feb 15: Discovered (96% match)                                    │
│ • Feb 10: Applied via LinkedIn                                      │
│ • Feb 17: Phone Screen (Scheduled)                                  │
│                                                                      │
│ 📝 NOTES:                                                            │
│ [Add Note] [View All Notes]                                         │
│                                                                      │
│ 🎯 NEXT STEPS:                                                       │
│ [✓] Prepare for phone screen                                        │
│ [✓] Research company values                                         │
│ [ ] Prepare questions for interviewer                               │
│                                                                      │
│ 📞 INTERVIEWS:                                                       │
│ Phone Screen - Feb 17, 10:00 AM with Sarah Chen                    │
│ [Add Interview] [View Details]                                      │
│                                                                      │
│ 🔔 REMINDERS:                                                        │
│ Follow up on Feb 24 if no response                                  │
│ [Add Reminder]                                                       │
├─────────────────────────────────────────────────────────────────────┤
│ [🔄 Update Status ▾] [📅 Schedule Interview] [📝 Add Note]          │
│ [⭐ Set Priority] [🔗 View Job] [🗑️ Archive]                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Status Update Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│ Update Status - AI Engineer @ Atlassian                            │
├─────────────────────────────────────────────────────────────────────┤
│ Current Status: 📤 Applied                                          │
│                                                                      │
│ New Status:                                                          │
│ ○ 💚 Interested                                                      │
│ ○ 📤 Applied (current)                                               │
│ ● 📧 Responded                                                       │
│ ○ 📞 Phone Screen                                                    │
│ ○ 🎯 Interview Scheduled                                             │
│ ○ 💼 Interviewed                                                     │
│ ○ 🔄 Follow-up                                                       │
│ ○ 🎉 Offer Received                                                  │
│ ○ ✅ Accepted                                                        │
│ ○ ❌ Declined Offer                                                  │
│ ○ 🚫 Rejected                                                        │
│                                                                      │
│ Notes (optional):                                                    │
│ [Received email response. Phone screen scheduled for Feb 17.     ]  │
│                                                                      │
│ Next Action Date:                                                    │
│ [📅 Feb 17, 2026] [Clear]                                           │
│                                                                      │
│           [Cancel]                        [Update Status]           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Schedule Interview Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│ Schedule Interview - AI Engineer @ Atlassian                        │
├─────────────────────────────────────────────────────────────────────┤
│ Interview Type:                                                      │
│ ○ Phone Screen  ● Video Call  ○ Onsite  ○ Panel Interview          │
│                                                                      │
│ Date & Time:                                                         │
│ [📅 Feb 17, 2026] [🕐 10:00 AM] [AWST ▾]                           │
│                                                                      │
│ Duration: [60] minutes                                               │
│                                                                      │
│ Interviewer(s):                                                      │
│ [Sarah Chen, Engineering Manager                                  ]  │
│ [+ Add Another Interviewer]                                          │
│                                                                      │
│ Meeting Link (if virtual):                                           │
│ [https://zoom.us/j/...                                            ]  │
│                                                                      │
│ Preparation Notes:                                                   │
│ [Review system design concepts                                    ]  │
│ [Prepare ML case study examples                                   ]  │
│ [Research Atlassian's AI products                                 ]  │
│                                                                      │
│ Set Reminder:                                                        │
│ ☑ 1 day before   ☑ 2 hours before   ☑ 30 mins before              │
│                                                                      │
│           [Cancel]                     [Schedule Interview]         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Dashboard Sidebar Navigation

```
┌─────────────────────┐
│ JOB TRACKER         │
├─────────────────────┤
│ 📊 Dashboard        │
│ 🔍 New Jobs (652)   │ ← Current view
│ 💚 Interested (23)  │
│ 📤 Applied (15)     │
│ 📞 Interviews (8)   │
│ 🎉 Offers (2)       │
│ ✅ Accepted (15)    │
│ 🚫 Rejected (30)    │
├─────────────────────┤
│ 📈 Analytics        │
│ ⚙️  Settings         │
└─────────────────────┘
```

---

## Analytics Dashboard

### Application Funnel
```
┌─────────────────────────────────────────────────────────────────────┐
│ APPLICATION FUNNEL (Last 30 Days)                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ New Jobs          ████████████████████████████████████ 652         │
│                   ↓ 23 (3.5%)                                        │
│ Interested        ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  23          │
│                   ↓ 15 (65%)                                         │
│ Applied           ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  15          │
│                   ↓ 8 (53%)                                          │
│ Interviewed       ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  8           │
│                   ↓ 2 (25%)                                          │
│ Offers            █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  2           │
│                   ↓ 2 (100%)                                         │
│ Accepted          █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  2           │
│                                                                      │
│ Conversion Rate: 0.31% (2 accepted / 652 discovered)                │
│ Success Rate: 13% (2 accepted / 15 applied)                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Time Metrics
```
┌─────────────────────────────────────────────────────────────────────┐
│ AVERAGE TIME IN EACH STAGE                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Discovery → Application:     3.2 days                               │
│ Application → Response:      5.8 days                               │
│ Response → Interview:        7.1 days                               │
│ Interview → Offer:          12.5 days                               │
│ Offer → Decision:            4.2 days                               │
│                                                                      │
│ Total Average: 32.8 days from discovery to hire                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technical Implementation

### Backend Routes (Flask)

```python
# Status management
@app.route('/job/<int:job_id>/status', methods=['POST'])
def update_job_status(job_id):
    """Update job status and log history"""
    
@app.route('/job/<int:job_id>/interview', methods=['POST'])
def schedule_interview(job_id):
    """Schedule interview for job"""
    
@app.route('/job/<int:job_id>/note', methods=['POST'])
def add_job_note(job_id):
    """Add note to job"""
    
@app.route('/job/<int:job_id>/priority', methods=['POST'])
def set_job_priority(job_id):
    """Set job priority (normal/high/urgent)"""

# View routes
@app.route('/status/<status>')
def jobs_by_status(status):
    """View jobs filtered by status"""
    
@app.route('/interviews')
def upcoming_interviews():
    """View upcoming interviews calendar"""
    
@app.route('/analytics')
def analytics_dashboard():
    """View analytics and metrics"""
```

### Database Functions

```python
# src/database.py additions
def update_job_status(job_id, new_status, notes=None):
    """Update status and log to history"""
    
def get_status_history(job_id):
    """Get status change history for job"""
    
def add_interview(job_id, interview_data):
    """Schedule interview"""
    
def get_upcoming_interviews(days=30):
    """Get interviews in next N days"""
    
def get_jobs_by_status(status):
    """Get all jobs with specific status"""
    
def get_application_stats():
    """Get funnel and conversion stats"""
```

---

## Implementation Priority

### Phase 1: Core Status Tracking (Week 1)
- [ ] Update database schema (new columns, tables)
- [ ] Add status update modal
- [ ] Status badges on job cards
- [ ] Status filter chips
- [ ] Status history logging

### Phase 2: Date Filtering (Week 1)
- [ ] Redesign date filter bar
- [ ] Add quick date filters (Today, Week, Month)
- [ ] Custom date range picker
- [ ] Visual timeline

### Phase 3: Interview Management (Week 2)
- [ ] Schedule interview modal
- [ ] Interview notes system
- [ ] Upcoming interviews view
- [ ] Interview reminders

### Phase 4: Advanced Features (Week 2)
- [ ] Kanban board view
- [ ] Priority system
- [ ] Notes system
- [ ] Follow-up reminders

### Phase 5: Analytics (Week 3)
- [ ] Application funnel
- [ ] Time metrics
- [ ] Success rate tracking
- [ ] Export reports

---

## Design Principles

1. **Mobile-First**: All features work on mobile
2. **Keyboard Shortcuts**: Power users can navigate quickly
3. **One-Click Actions**: Most common actions require one click
4. **Visual Clarity**: Status is immediately obvious from colors/icons
5. **No Information Loss**: All tracking data preserved forever
6. **Undo Support**: Critical actions can be undone

---

## Color Coding

```css
Status Colors:
- NEW: #64748b (gray)
- INTERESTED: #10b981 (green)
- APPLIED: #3b82f6 (blue)
- RESPONDED: #8b5cf6 (purple)
- PHONE_SCREEN: #f59e0b (amber)
- INTERVIEW: #ec4899 (pink)
- INTERVIEWED: #6366f1 (indigo)
- OFFER: #14b8a6 (teal)
- ACCEPTED: #22c55e (lime)
- REJECTED: #ef4444 (red)
- ON_HOLD: #f97316 (orange)
```

---

## Success Metrics

After implementation, track:
- Time saved per job application
- Application success rate improvement
- Number of missed follow-ups (should → 0)
- User engagement with tracking features
- Dashboard load time (<2s)

---

**Ready to implement? This is a complete Application Tracking System that rivals paid ATS platforms!** 🚀
