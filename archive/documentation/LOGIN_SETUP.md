# Login Setup Guide

This guide explains how to set up persistent login sessions for LinkedIn and Seek scrapers.

## 🔑 Quick Start

### First-Time Setup (One-Time Only)

#### 1. LinkedIn Login
```bash
python linkedin_login.py
```
- Opens a browser window
- Login to your LinkedIn account
- Complete any 2FA/security checks
- Press Enter when done
- Session saved to `data/linkedin_cookies.pkl`

#### 2. Seek Login
```bash
python seek_login.py
```
- Opens a browser window
- Click "Sign in" in top right
- Login to your Seek account
- Press Enter when done
- Session saved to `data/seek_cookies.pkl`

### That's It! 🎉

After running these scripts once, your scraping will automatically use the saved sessions.

## 📋 How It Works

### Persistent Cookies
Both scrapers automatically load saved cookies when initialized:

**LinkedIn Scraper** ([src/scraper.py](src/scraper.py)):
- Loads `data/linkedin_cookies.pkl` automatically
- Uses Selenium WebDriver with saved session
- No need to login for each scrape

**Seek Scraper** ([src/seek_scraper.py](src/seek_scraper.py)):
- Loads `data/seek_cookies.pkl` automatically  
- Uses requests library with saved cookies
- Session persists across runs

### Cookie Lifespan

**How long do cookies last?**
- LinkedIn: ~30 days (varies by account settings)
- Seek: ~30 days (varies by account settings)

**When do I need to re-login?**
You'll know cookies expired when you see errors like:
- "Login required"
- "Session expired"
- "Authentication failed"
- Empty results or blocked requests

Just re-run the login script:
```bash
# For LinkedIn
python linkedin_login.py

# For Seek
python seek_login.py
```

## 🔒 Security Notes

### Cookie Files
The cookie files are stored locally:
- `data/linkedin_cookies.pkl`
- `data/seek_cookies.pkl`

**⚠️ IMPORTANT:**
- These files contain your session credentials
- Keep them private (already in `.gitignore`)
- Never commit them to version control
- Don't share them with others

### What's Stored?
The cookie files contain:
- Session tokens
- Authentication cookies
- User preferences
- **NOT** your username/password

## 🛠️ Troubleshooting

### "No saved cookies found"
**Solution:** Run the login script first
```bash
python linkedin_login.py  # or seek_login.py
```

### "Login verification failed"
**Possible causes:**
1. Didn't complete login process fully
2. Security challenge not completed
3. Browser closed too early

**Solution:**
1. Re-run the login script
2. Make sure you see your profile/homepage before pressing Enter
3. Wait for all redirects to complete

### "Session expired" during scraping
**Solution:** Cookies expired, re-run login:
```bash
python linkedin_login.py
python seek_login.py
```

### Can't access login scripts
**Make them executable:**
```bash
chmod +x linkedin_login.py seek_login.py
```

## 🚀 Running Scrapes

Once logged in, run scrapes normally:

```bash
# Test scraping
python test_6_urls.py

# Full scrape
python src/main.py

# Dashboard
python src/dashboard.py
```

The scrapers will automatically use your saved sessions!

## 📊 Check Login Status

**Check if cookies exist:**
```bash
ls -lh data/*_cookies.pkl
```

**Check cookie age:**
```bash
# macOS
stat -f "%Sm" data/linkedin_cookies.pkl
stat -f "%Sm" data/seek_cookies.pkl

# Linux
stat -c "%y" data/linkedin_cookies.pkl
```

**If cookies are >30 days old, re-run login scripts**

## 🔄 Alternative: Chrome Profile (Advanced)

Instead of cookie files, you can use a dedicated Chrome profile:

1. **Create profile:** The scraper creates `chrome_profile/` folder
2. **First run:** Login manually in the browser
3. **Future runs:** Session persists in profile

**Note:** Can't use your main Chrome profile while Chrome is running.

## ❓ FAQ

**Q: Do I need to provide my username/password to the scripts?**  
A: No! You login manually in the browser. The script just saves the session.

**Q: Can I automate the login?**  
A: Not recommended. LinkedIn/Seek have anti-bot measures. Manual login is safer.

**Q: How secure is this?**  
A: Same as keeping your browser open. Cookie files are encrypted by the OS file system.

**Q: Can I run scrapes on a server/headless?**  
A: Yes! Run login scripts on your local machine first, then copy the cookie files to the server:
```bash
scp data/*_cookies.pkl user@server:/path/to/Job_Scrape/data/
```

**Q: What if LinkedIn/Seek detects scraping?**  
A: Use reasonable delays (already implemented). Don't scrape too frequently.

## 📝 Summary

| Step | Command | Frequency |
|------|---------|-----------|
| Setup LinkedIn | `python linkedin_login.py` | Once (+ when expired) |
| Setup Seek | `python seek_login.py` | Once (+ when expired) |
| Run scrapes | `python src/main.py` | Anytime |
| Re-login | Re-run login scripts | ~Every 30 days |

**You're all set! Happy scraping! 🎉**
