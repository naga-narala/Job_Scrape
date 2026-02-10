# Future Improvements

## Dashboard Issues



---

### 2. Apply Button Shows LinkedIn for All Jobs
**Current Behavior**: "Apply on LinkedIn" button appears for jobs scraped from Jora and Seek.

**Expected Behavior**: Button text and link should match the job source platform.

**Proposed Solution**:
- Add conditional button rendering based on `source` field in database
- Show "Apply on Seek", "Apply on Jora", or "Apply on LinkedIn" accordingly
- Consider adding platform icon/badge to make source immediately visible

**Files to Modify**:
- [templates/dashboard.html](templates/dashboard.html) - Update button rendering logic
- Ensure `source` field is properly stored in database during scraping

**Implementation Example**:
```html
{% if job.source == 'linkedin' %}
  <a href="{{ job.url }}" class="apply-btn linkedin">Apply on LinkedIn</a>
{% elif job.source == 'seek' %}
  <a href="{{ job.url }}" class="apply-btn seek">Apply on Seek</a>
{% elif job.source == 'jora' %}
  <a href="{{ job.url }}" class="apply-btn jora">Apply on Jora</a>
{% endif %}
```



### 3. Job Deduplication Across Platforms
**Issue**: Same job may appear on LinkedIn, Seek, and Jora with different URLs.

**Proposed Solution**:
- Enhance `generate_job_hash()` to normalize company names and titles
- Add fuzzy matching for similar job descriptions
- Mark duplicates and link to original posting

---







### 7. Analytics Dashboard
**Proposed Features**:
- Jobs scraped per day/week/month (by platform)
- Score distribution histogram
- Most common rejection reasons
- Application success rate tracking
- Time-to-apply metrics (how quickly you apply after job is posted)

---




---

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on implementing these improvements.
