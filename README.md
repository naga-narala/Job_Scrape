# LinkedIn Job Scraper with AI Matching

Automated job search system that monitors multiple LinkedIn job searches, scores them against your profile using AI, and alerts you to high-confidence matches (75%+). Runs locally, completely free using your existing API credits.

## 🎯 Features

- **Multi-Source Job Fetching**: RSSHub → Brave Search API → Direct Scraping fallback chain
- **AI-Powered Matching**: Uses OpenRouter (Gemini Flash 8B primary) to score jobs 0-100%
- **Smart Auto-Rescoring**: When you update your profile, automatically re-scores recent jobs (70-79%, <7 days old)
- **Dual Notification System**: Email alerts (with 3 retries) + HTML file fallback that auto-opens in browser
- **Day-Wise Dashboard**: Clean UI showing "Today", "Yesterday", etc. with 7-day default view
- **Auto-Hide Old Jobs**: Jobs older than 30 days are hidden (still in database)
- **Application Tracking**: Mark jobs as "Applied" to keep track
- **Perth Timezone**: All timestamps in AWST (Australia/Perth)
- **Docker Ready**: Easy deployment with docker-compose

## 📋 Requirements

- Python 3.11+
- OpenRouter API key (you have this)
- Brave Search API key (optional, you have this)
- Gmail account with app password (for email alerts)

## 🚀 Quick Start (Local)

### 1. Install Dependencies

```bash
cd /Users/b/Desktop/Projects/Job_Scrape
pip install -r requirements.txt
```

### 2. Configure the System

#### a) Edit `config.json`
```bash
# Add your API keys and email settings
{
  "openrouter_api_key": "YOUR_KEY_HERE",
  "brave_search_api_key": "YOUR_KEY_HERE",
  "email_from": "your@gmail.com",
  "email_password": "your-app-password",
  "email_to": "your@gmail.com"
}
```

**Gmail App Password Setup:**
1. Go to Google Account → Security → 2-Step Verification
2. Scroll to "App passwords" → Generate new
3. Select "Mail" → Copy the 16-character password
4. Use this (NOT your regular Gmail password) in `config.json`

#### b) Add Your Job Searches to `job_searches.json`
```json
{
  "searches": [
    {
      "id": "ml_engineer_india",
      "name": "Junior ML Engineer - India",
      "url": "https://www.linkedin.com/jobs/search-results/?f_TPR=r86400&geoId=103392068&keywords=Junior%20Machine%20learning%20engineer",
      "enabled": true
    },
    {
      "id": "data_scientist_bangalore",
      "name": "Data Scientist - Bangalore",
      "url": "YOUR_LINKEDIN_URL_HERE",
      "enabled": true
    }
  ]
}
```

**How to get LinkedIn URLs:**
1. Go to linkedin.com/jobs
2. Search for your job (e.g., "Python Developer")
3. Apply filters (location, experience level, remote, etc.)
4. Copy the full URL from address bar
5. Paste into `job_searches.json`

#### c) Add Your Resume to `profile.txt`
```bash
# Open profile.txt and paste:
- Your full resume
- Skills (Python, TensorFlow, etc.)
- Experience
- Education
- Job preferences (remote, salary, company size)
- Must-have requirements
- Deal-breakers
```

### 3. Test the Setup

```bash
python src/main.py --test
```

This will:
- ✓ Validate configuration
- ✓ Fetch 3 sample jobs
- ✓ Score them with AI
- ✓ Send test email
- ✓ Show results

### 4. Run the System

**Start Dashboard (in one terminal):**
```bash
python src/dashboard.py
```

**Start Automation (in another terminal):**
```bash
python src/main.py --daemon
```

**Access Dashboard:**
Open browser to `http://localhost:5000`

## 🐳 Quick Start (Docker)

### 1. Configure Files
Same as local setup (steps 2a, 2b, 2c above)

### 2. Build and Run
```bash
docker-compose up -d
```

### 3. Access Dashboard
Open browser to `http://localhost:5000`

### 4. View Logs
```bash
docker-compose logs -f job-scraper
```

### 5. Stop
```bash
docker-compose down
```

## 📊 How It Works

### Daily Automated Workflow (Every 24 Hours)

1. **Profile Change Detection**: Checks if `profile.txt` changed
2. **Smart Rescore**: Re-scores jobs that scored 70-79% and are <7 days old
3. **Fetch Jobs**: Gets jobs from all LinkedIn searches using fallback chain
4. **Deduplication**: Skips jobs already in database (same title+company+url)
5. **AI Scoring**: Scores new jobs 0-100% against your profile
6. **Filter Matches**: Finds jobs ≥75%
7. **Send Alerts**: Emails you new matches (or opens HTML in browser if email fails)

### What Happens to Jobs

```
New Job → Fetch → Deduplicate → Score → Filter (≥75%) → Email Alert → Dashboard
                                              ↓
                                        Score <75% → Dashboard only (no email)
```

### Profile Updates

When you edit `profile.txt`:
- System detects change on next run
- Re-scores jobs that scored 70-79% and are <7 days old
- If any upgrade to 75%+, you get email alert
- Prevents wasted API calls on old/irrelevant jobs

## 🎨 Dashboard Features

### Main View (http://localhost:5000)
- Jobs grouped by day: "Today", "Yesterday", "3 days ago", etc.
- Default: Last 7 days (configurable)
- Color-coded scores: Green (90%+), Yellow (80-89%), Gray (75-79%)
- Click job title → Opens LinkedIn
- "Mark as Applied" button
- "Re-score" button (uses current profile)

### Statistics Page (http://localhost:5000/stats)
- Total jobs tracked
- High matches count (75%+)
- Average score
- Score distribution (90%+, 80-89%, 75-79%, <75%)
- Top companies

### Filters
- Last 7 Days (default)
- Last 30 Days
- All Jobs (everything in database)

## 📁 Project Structure

```
Job_Scrape/
├── config.json              # Your API keys, settings
├── job_searches.json        # LinkedIn URLs to monitor
├── profile.txt              # Your resume & preferences
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker container config
├── docker-compose.yml       # Docker deployment
├── src/
│   ├── main.py             # Main orchestrator & scheduler
│   ├── database.py         # SQLite operations
│   ├── scraper.py          # Multi-strategy job fetcher
│   ├── scorer.py           # OpenRouter AI scoring
│   ├── rescore_manager.py  # Smart profile-based rescoring
│   ├── notifier.py         # Email + HTML notifications
│   └── dashboard.py        # Flask web server
├── templates/
│   ├── dashboard.html      # Main UI
│   └── stats.html          # Statistics page
└── data/                   # Created at runtime
    ├── jobs.db            # SQLite database
    ├── logs/              # job_scraper.log
    └── notifications/     # HTML alerts (if email fails)
```

## 🔧 Configuration Options

### config.json Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `match_threshold` | 75 | Minimum score to send alerts |
| `check_interval_hours` | 24 | How often to check for jobs |
| `rescore_threshold_min` | 70 | Min score for auto-rescore |
| `rescore_threshold_max` | 79 | Max score for auto-rescore |
| `rescore_max_age_days` | 7 | Max age for auto-rescore |
| `hide_jobs_older_than_days` | 30 | Auto-hide old jobs |
| `dashboard_default_days` | 7 | Default dashboard view |

### AI Model Fallback Chain

1. **Primary**: `google/gemini-flash-1.5-8b` (~$0.0375 per 1M tokens)
2. **Fallback 1**: `google/gemini-flash-1.5` (~$0.075 per 1M tokens)
3. **Fallback 2**: `anthropic/claude-3.5-haiku` (~$0.80 per 1M tokens)
4. **Fallback 3**: `meta-llama/llama-3.3-70b-instruct` (~$0.35 per 1M tokens)

**Cost Estimate**: Scoring 100 jobs ≈ $0.05-0.15 with Gemini Flash 8B

## 🛠️ Usage Commands

### Local Execution

```bash
# Test configuration (run first!)
python src/main.py --test

# Run once immediately (no scheduling)
python src/main.py --run-now

# Run as daemon (every 24h)
python src/main.py --daemon

# Start dashboard only
python src/dashboard.py
```

### Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

## 📝 Adding More Job Searches

Edit `job_searches.json`:

```json
{
  "searches": [
    {
      "id": "unique_id_here",
      "name": "Descriptive Name",
      "url": "https://www.linkedin.com/jobs/search-results/?...",
      "enabled": true
    }
  ]
}
```

**Tips:**
- Use unique `id` for each search (e.g., `ml_engineer_remote`)
- Set `enabled: false` to temporarily disable a search
- System checks all enabled searches every 24h
- No limit on number of searches!

## 🔍 Troubleshooting

### No Jobs Fetched
- **Check LinkedIn URLs**: Make sure they're valid and public
- **Check Logs**: `data/logs/job_scraper.log` shows what failed
- **RSSHub Down?**: System will try Brave API, then direct scraping
- **All Failed?**: Check network connection

### Email Not Working
- **Use App Password**: NOT your regular Gmail password
- **Enable 2FA**: Gmail requires 2-step verification for app passwords
- **Check SMTP Settings**: Default is `smtp.gmail.com:587`
- **Fallback Works**: If email fails, HTML file auto-opens in browser

### Low/No Match Scores
- **Update Profile**: Add more details to `profile.txt`
- **Check Threshold**: Default is 75%, maybe try 70%
- **Recent Jobs?**: Auto-rescore will catch them if you update profile
- **View All Jobs**: Go to `/all` to see jobs below threshold

### Dashboard Empty
- **Run Scraper First**: `python src/main.py --run-now`
- **Check Threshold**: Jobs below 75% won't show by default
- **Check Date Range**: Default is 7 days, try "All Jobs"

### Database Issues
- **Delete and Restart**: `rm data/jobs.db` then run again
- **Permission Error**: Check `data/` directory exists and is writable

## 📊 Database Schema

Located at: `data/jobs.db` (SQLite)

**Tables:**
- `jobs`: All fetched jobs
- `scores`: AI match scores
- `notifications`: Email/HTML alert history
- `profile_changes`: Profile update tracking

**To inspect:**
```bash
sqlite3 data/jobs.db
sqlite> .tables
sqlite> SELECT * FROM jobs LIMIT 5;
```

## 🔐 Security Notes

- **Never commit config.json**: Contains API keys (in .gitignore)
- **Use .env for Docker**: Copy `.env.example` → `.env` with real keys
- **App Passwords**: Safer than real Gmail password
- **Local Only**: Dashboard runs on localhost (not internet-facing)

## 🚀 Next Steps

1. **Test Everything**: `python src/main.py --test`
2. **Add Your Searches**: Edit `job_searches.json` with 10+ LinkedIn URLs
3. **Paste Resume**: Fill `profile.txt` with detailed info
4. **Start System**: Run daemon + dashboard
5. **Check Dashboard**: http://localhost:5000
6. **Wait 24h**: System will run automatically

## 💡 Tips for Best Results

### Profile.txt
- Be detailed! More info = better scores
- Include soft skills (teamwork, communication)
- List all tools/frameworks you know
- Mention preferences (remote, startup, etc.)
- Add deal-breakers (must sponsor visa, etc.)

### Job Searches
- Start with 5-10 searches, expand from there
- Use LinkedIn's filters (location, experience, remote)
- Include time filter `f_TPR=r86400` (last 24h) for freshness
- Try variations: "ML Engineer" vs "Machine Learning Engineer"

### Monitoring
- Check logs daily: `tail -f data/logs/job_scraper.log`
- Review dashboard weekly
- Update profile monthly as you learn new skills
- Adjust threshold if too many/few matches

## 🐛 Known Issues

- **LinkedIn HTML Changes**: Direct scraping may break (RSSHub/Brave are primary)
- **RSSHub Rate Limits**: Free tier limited, consider self-hosting RSSHub
- **Email Delays**: Gmail may throttle if sending too many alerts

## 📜 License

MIT License - Use freely, no attribution required.

## 🙋 Support

Check logs first: `data/logs/job_scraper.log`

Common log messages:
- `✓ RSSHub: Fetched X jobs` → Working!
- `RSSHub failed, trying Brave` → Normal fallback
- `All fetch strategies failed` → Check network/URLs
- `Email sent successfully` → Alerts working
- `Email failed, using HTML` → Fallback working

---

**Built with:** Python, Flask, SQLite, OpenRouter AI, RSSHub, BeautifulSoup

**Runs on:** macOS, Linux, Docker (Windows via Docker)

**Cost:** Free (uses your OpenRouter credits, ~$0.05-0.15 per 100 jobs)
