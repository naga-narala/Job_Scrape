# Job Scraper - Scalable Architecture Design

**Current:** Single-user local application  
**Future:** Multi-tenant SaaS platform for global users  
**Design Principle:** Build for scale NOW, avoid refactoring LATER

---

## 🏗️ Multi-Tenant Ready Architecture

### Current Structure (Single User)
```
/Job_Scrape/
├── jobs.txt                    # User's target job titles
├── profile.txt                 # User's personal profile
├── config.json                 # Application config
├── generated_keywords.json     # Auto-generated from jobs.txt
├── data/
│   ├── jobs.db                # SQLite database
│   ├── logs/
│   └── notifications/
└── src/
    ├── keyword_generator.py
    ├── scraper.py
    ├── scorer.py
    └── ...
```

### Future Structure (Multi-User SaaS)
```
/Job_Scraper_Platform/
├── config/
│   └── app_config.json        # Global app settings
├── users/
│   ├── user_001/
│   │   ├── jobs.txt           # User 1's target roles
│   │   ├── profile.txt        # User 1's profile
│   │   ├── generated_keywords.json
│   │   └── data/
│   │       └── jobs.db        # User 1's database
│   ├── user_002/
│   │   ├── jobs.txt
│   │   ├── profile.txt
│   │   ├── generated_keywords.json
│   │   └── data/
│   │       └── jobs.db
│   └── ...
├── shared/
│   ├── src/                   # Shared codebase
│   └── templates/
└── web/
    ├── backend/               # FastAPI/Flask backend
    ├── frontend/              # React/Vue frontend
    └── database/              # PostgreSQL (multi-tenant)
```

---

## 📋 Enhanced jobs.txt Format

### Current Format (Simple)
```
Graduate AI Engineer, Junior ML Engineer, Data Scientist
```

### Future Format (Metadata-Rich)
```
# Target Job Titles
Graduate AI Engineer, Junior ML Engineer, Graduate Data Scientist

# Dealbreakers (Optional - if not specified, general search applies)
# EXPERIENCE: Maximum years of experience required (e.g., 0-2)
# SENIORITY: Levels to exclude (e.g., Senior, Lead, Principal, Manager)
# VISA: Citizenship/visa requirements to exclude (e.g., PR Required, Citizenship Required, US Citizen Only)
# EDUCATION: Degrees to exclude if you don't have (e.g., PhD Required)
# CERTIFICATIONS: Licenses to exclude (e.g., CPA Required, Bar Admission)

[DEALBREAKERS]
max_experience: 2
exclude_seniority: Senior, Lead, Principal, Manager, Director, Head of, Chief
exclude_visa: PR Required, Permanent Resident, Citizenship, US Citizen, Security Clearance
exclude_education: PhD Required, Doctorate Required
exclude_certifications: 

# Search Preferences (Optional)
[PREFERENCES]
regions: australia, us
locations: Perth, Melbourne, Remote
job_boards: linkedin, seek, jora

# Optimization Settings (Optional - defaults if not specified)
[OPTIMIZATION]
# NOTE: By providing detailed dealbreakers above, the workflow can optimize:
# - Skip irrelevant jobs faster (saves runtime)
# - Reduce AI API costs (don't score unsuitable jobs)
# - Improve match quality (context-aware filtering)
enable_title_filtering: true
enable_description_filtering: true
enable_deduplication: true
optimization_level: balanced  # balanced, conservative, aggressive
```

---

## 🗄️ Database Design (Multi-Tenant Ready)

### Current: Single SQLite Database
```sql
-- Single user, simple schema
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    title TEXT,
    company TEXT,
    ...
);
```

### Future: PostgreSQL Multi-Tenant
```sql
-- Multi-tenant with user isolation
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    created_at TIMESTAMP,
    subscription_tier TEXT,  -- free, pro, enterprise
    ...
);

CREATE TABLE user_profiles (
    profile_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    profile_data JSONB,  -- Flexible profile storage
    created_at TIMESTAMP
);

CREATE TABLE jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),  -- Partition by user
    title TEXT,
    company TEXT,
    source TEXT,  -- linkedin, seek, jora
    region TEXT,
    ...
    INDEX idx_user_jobs (user_id, created_at)
);

CREATE TABLE generated_keywords (
    keyword_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    jobs_txt_hash TEXT,  -- Detect changes
    keywords_data JSONB,
    generated_at TIMESTAMP
);
```

---

## 🔧 Code Architecture (Service Layer Pattern)

### Current: Monolithic Functions
```python
# scraper.py
def scrape_jobs():
    # Hardcoded everything
    profile = read_profile()
    jobs = scrape_linkedin()
```

### Future: Service-Oriented (Easy to Scale)
```python
# services/user_service.py
class UserService:
    def get_user_profile(self, user_id):
        pass
    
    def get_user_jobs_config(self, user_id):
        pass

# services/keyword_service.py
class KeywordService:
    def generate_keywords(self, user_id, jobs_txt):
        pass
    
    def get_cached_keywords(self, user_id):
        pass

# services/scraper_service.py
class ScraperService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.keywords = KeywordService().get_cached_keywords(user_id)
        
    def scrape_all_sources(self):
        pass

# main.py
def run_for_user(user_id):
    scraper = ScraperService(user_id)
    scraper.scrape_all_sources()
```

---

## 🔐 Security & Isolation (Multi-Tenant)

### Data Isolation Strategies

1. **Database Level:** Separate database per user (expensive, max isolation)
2. **Schema Level:** Separate schema per user (PostgreSQL schemas)
3. **Table Level:** user_id in every table (current plan, most scalable)
4. **Row-Level Security:** PostgreSQL RLS policies

**Chosen:** Table-level with user_id + Row-Level Security

```sql
-- PostgreSQL Row-Level Security
CREATE POLICY user_isolation ON jobs
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

---

## 🚀 Migration Path (Current → SaaS)

### Phase 1: Single User (NOW)
- ✅ Use current structure
- ✅ Design code with service pattern
- ✅ Use keyword generation
- ✅ Enhanced jobs.txt format

### Phase 2: Local Multi-User
- Move to `users/user_001/` structure
- Add user management commands
- Shared codebase in `shared/src/`

### Phase 3: Web API (Backend)
- FastAPI backend
- REST API endpoints
- User authentication (JWT)
- API rate limiting

### Phase 4: Full SaaS Platform
- React/Vue frontend
- PostgreSQL database
- User subscriptions (Stripe)
- Cloud deployment (AWS/GCP)
- Monitoring & analytics

---

## 📊 Scalability Considerations

### Current Constraints
- SQLite: Single user, ~1M jobs max
- Local filesystem: Single machine
- No concurrent users

### Future Requirements
- PostgreSQL: Multi-user, billions of jobs
- Cloud storage (S3): Distributed files
- Redis: Caching, session management
- Celery: Background job queue
- Load balancing: Multiple API servers

### Performance Targets
- **Current:** 2,000 jobs/run, 60 min
- **SaaS Free Tier:** 5,000 jobs/day, 10 users
- **SaaS Pro Tier:** 50,000 jobs/day, 1000 concurrent users
- **SaaS Enterprise:** Unlimited, 10K+ concurrent users

---

## 🎯 Current Implementation Strategy

**For NOW (v1.0 - Single User):**

1. ✅ Keep current file structure (jobs.txt, profile.txt, config.json)
2. ✅ Add generated_keywords.json (auto-generated from jobs.txt)
3. ✅ Use service pattern in code (easy to extract later)
4. ✅ Enhanced jobs.txt with metadata support
5. ✅ Balanced filtering (Tier 1, 2, 3)

**Code should be:**
- ✅ Modular (easy to extract services)
- ✅ User-agnostic (works for any role)
- ✅ Config-driven (no hardcoded values)
- ✅ Database-ready (SQLite → PostgreSQL later)

**What to AVOID:**
- ❌ Hardcoded AI/ML keywords
- ❌ Hardcoded dealbreakers
- ❌ Direct file reads (use abstraction)
- ❌ Global state variables

---

## 📝 File Naming Conventions

### Current (Single User)
```
jobs.txt
profile.txt
config.json
generated_keywords.json
data/jobs.db
```

### Future (Multi-User)
```
users/{user_id}/jobs.txt
users/{user_id}/profile.txt
users/{user_id}/generated_keywords.json
users/{user_id}/data/jobs.db
config/app_config.json (shared)
```

---

## 🔄 Keyword Generation Flow

```
jobs.txt changes → Detect via hash → Generate keywords via AI → Save to generated_keywords.json → All modules reload keywords

Current (Single User):
1. User edits jobs.txt
2. Run: python src/main.py
3. System detects jobs.txt change (hash comparison)
4. Generate keywords via DeepSeek API (~$0.01)
5. Save to generated_keywords.json
6. Workflow uses new keywords

Future (Multi-User SaaS):
1. User edits jobs.txt via web UI
2. Backend detects change
3. Queue keyword generation job (Celery)
4. Generate keywords (cached)
5. Save to database
6. Notify user via websocket
7. Next scrape uses new keywords
```

---

## 🎨 UI/UX Future Vision

### Dashboard Evolution

**Current:** Simple Flask HTML dashboard
- Job list with scores
- Filters (region, location, time)
- Apply/Applied tracking

**Future SaaS:**
- Rich React/Vue dashboard
- Real-time scraping progress (websockets)
- Advanced filters (salary, tech stack, company size)
- Job comparison tool
- Application tracking timeline
- Analytics dashboard (match trends, best sources)
- AI chat assistant for job search advice
- Browser extension for one-click applications

---

## 💰 Monetization Strategy (Future)

### Tier Structure

**Free Tier:**
- 1 job role search
- LinkedIn only
- 100 jobs/day
- 7-day history
- Email notifications

**Pro Tier ($19/month):**
- 5 job role searches
- LinkedIn + Seek + Jora
- 1,000 jobs/day
- 30-day history
- Email + SMS notifications
- Priority support

**Enterprise ($99/month):**
- Unlimited role searches
- All job boards + custom integrations
- Unlimited jobs
- Unlimited history
- API access
- Dedicated support
- Custom dealbreakers
- Team accounts

---

## 🔒 Current Implementation Guardrails

To ensure smooth future migration:

1. **No Hardcoded Paths:** Use config-driven paths
2. **Service Pattern:** Wrap all operations in services
3. **Database Abstraction:** Use ORM-like patterns
4. **Config-Driven:** Everything in config/generated files
5. **User Context:** Pass user context everywhere (even if single user now)
6. **Logging:** Structured logging (JSON format)
7. **Error Handling:** Graceful degradation
8. **API-Ready:** Functions return data, not print statements

---

## 📚 Technology Stack Roadmap

### Current (v1.0)
- Python 3.13
- SQLite
- Selenium
- Flask
- DeepSeek API

### Near Future (v2.0 - Multi-User Local)
- Same stack
- Better file organization
- User management

### SaaS Platform (v3.0)
- **Backend:** FastAPI, PostgreSQL, Redis, Celery
- **Frontend:** React/Next.js, TailwindCSS
- **Deployment:** Docker, Kubernetes, AWS/GCP
- **Auth:** Auth0 / Supabase
- **Payment:** Stripe
- **Monitoring:** Sentry, DataDog
- **CI/CD:** GitHub Actions

---

## ✅ Summary: What We're Building NOW

**v1.0 Goals (Current Sprint):**
1. ✅ Enhanced jobs.txt format (with metadata)
2. ✅ Keyword generator (AI-powered, role-agnostic)
3. ✅ Balanced filtering (Tier 1, 2, 3 optimization)
4. ✅ Service pattern code structure
5. ✅ Config-driven workflow
6. ✅ User-agnostic design (works for any role)

**Future-Ready Features:**
- ✅ File structure ready for multi-user
- ✅ Code can be extracted into services
- ✅ Database schema can migrate to PostgreSQL
- ✅ No refactoring needed for SaaS transition

**Next Steps:**
1. Implement keyword generator
2. Refactor to use generated keywords
3. Add balanced filtering
4. Test with different job roles (AI, Finance, Marketing)
5. Document migration process
