import requests
import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Load config
config_path = Path(__file__).parent.parent / 'config.json'
with open(config_path, 'r') as f:
    _SCORER_CONFIG = json.load(f)

# Import job parser for hard filtering
try:
    from job_parser import JobDescriptionParser
    PARSER_AVAILABLE = True
except ImportError:
    logger.warning("JobDescriptionParser not available - dealbreaker filtering disabled")
    PARSER_AVAILABLE = False

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_keywords():
    """Load keywords from generated_keywords.json (role-agnostic)"""
    keywords_path = Path(__file__).parent.parent / 'generated_keywords.json'
    try:
        with open(keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            'title_keywords': data.get('title_keywords', []),
            'strong_keywords': data.get('strong_keywords', []),
            'technical_skills': data.get('technical_skills', []),
            'adjacent_roles': data.get('adjacent_roles', [])
        }
    except FileNotFoundError:
        logger.warning("generated_keywords.json not found - using fallback keywords")
        return {
            'title_keywords': ['ai', 'ml', 'data scientist'],
            'strong_keywords': ['machine learning', 'deep learning'],
            'technical_skills': ['python', 'pytorch', 'tensorflow'],
            'adjacent_roles': []
        }


def load_jobs_txt_metadata():
    """Load dealbreakers and preferences from jobs.txt"""
    jobs_txt_path = Path(__file__).parent.parent / 'jobs.txt'
    metadata = {
        'max_experience': 2,
        'exclude_seniority': ['Senior', 'Lead', 'Principal'],
        'exclude_visa': ['PR Required', 'Citizenship Required'],
        'locations': ['Perth', 'Melbourne', 'Remote']
    }
    
    try:
        with open(jobs_txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse dealbreakers
        if '[DEALBREAKERS]' in content:
            dealbreakers_section = content.split('[DEALBREAKERS]')[1].split('[PREFERENCES]')[0] if '[PREFERENCES]' in content else content.split('[DEALBREAKERS]')[1]
            
            for line in dealbreakers_section.split('\n'):
                if line.strip().startswith('max_experience:'):
                    try:
                        metadata['max_experience'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif line.strip().startswith('exclude_seniority:'):
                    seniority = line.split(':', 1)[1].strip()
                    metadata['exclude_seniority'] = [s.strip() for s in seniority.split(',')]
                elif line.strip().startswith('exclude_visa:'):
                    visa = line.split(':', 1)[1].strip()
                    metadata['exclude_visa'] = [v.strip() for v in visa.split(',')]
        
        # Parse preferences
        if '[PREFERENCES]' in content:
            prefs_section = content.split('[PREFERENCES]')[1].split('[OPTIMIZATION]')[0] if '[OPTIMIZATION]' in content else content.split('[PREFERENCES]')[1]
            
            for line in prefs_section.split('\n'):
                if line.strip().startswith('locations:'):
                    locs = line.split(':', 1)[1].strip()
                    metadata['locations'] = [l.strip() for l in locs.split(',')]
        
    except Exception as e:
        logger.warning(f"Could not parse jobs.txt metadata: {e}")
    
    return metadata


def build_dynamic_prompt_template():
    """Build prompt template with dynamic keywords (role-agnostic)"""
    keywords = load_keywords()
    metadata = load_jobs_txt_metadata()
    
    # Build role list from title_keywords and adjacent_roles
    role_list = ', '.join(keywords['title_keywords'] + keywords['adjacent_roles'])
    
    # Build strong keywords list
    strong_keywords_list = ', '.join(keywords['strong_keywords'])
    
    # Build technical skills list
    technical_skills_list = ', '.join(keywords['technical_skills'][:20])  # Top 20 for readability
    
    # Build seniority exclusions
    seniority_list = '/'.join(metadata['exclude_seniority'][:10])  # Top 10
    
    # Build locations preference
    locations_list = ' > '.join(metadata['locations'])
    
    max_exp = metadata['max_experience']
    
    return f"""You are an expert job matching assistant. Analyze how well this job matches the candidate's profile using EXTREMELY STRICT scoring criteria.

CANDIDATE PROFILE:
{{profile_content}}

JOB POSTING:
Title: {{job_title}}
Company: {{job_company}}
Location: {{job_location}}
Description: {{job_description}}

⚠️ CRITICAL SCORING CRITERIA - APPLY WITH ZERO TOLERANCE ⚠️

AUTOMATIC REJECTION (Score 0-30) - BE EXTREMELY STRICT:
- NOT a target role - Must match one of these or closely related: {role_list}
- Requires Australian PR/Citizenship/Security Clearance (candidate has 485 visa with full work rights - NOT a citizen)
- Requires {max_exp}+ years professional experience (candidate is FRESH GRADUATE - only academic projects)
- Requires {max_exp+1}+ years in ANY technology (candidate has NO professional experience)
- Requires {max_exp+2}+ years, {max_exp+3}+ years, or more (ABSOLUTE DEALBREAKER for fresh graduate)
- {seniority_list} position (candidate needs GRADUATE or JUNIOR level ONLY)
- "Preference for citizens" or "citizens preferred" (candidate only has 485 visa, not PR or citizen)
- Role outside target domain with no relevant component

🚨 IF ANY OF THE ABOVE APPLY, SCORE MUST BE 0-30. NO EXCEPTIONS. 🚨

LOW MATCH (Score 40-60):
- Heavy focus on unfamiliar technologies (candidate learning new stack)
- Role without core technical component
- Full-stack or general development as primary skill
- Location outside preference without remote option
- No mention of visa flexibility for 485 holders
- Missing key technical requirements from candidate's stack
- Requires 1-{max_exp} years experience (borderline for fresh graduate)

HIGH MATCH (Score 70-100):
MUST have most of these:
- Junior/Graduate/Entry-level explicitly mentioned OR "0-{max_exp} years" OR "fresh graduate welcome"
- Core technologies required: {technical_skills_list}
- Strong keywords: {strong_keywords_list}
- Location: {locations_list}
- "Visa sponsorship available" OR "485 visa acceptable" OR no visa requirements mentioned
- Growth potential, mentorship opportunities, learning environment

Analyze the job and provide:
1. Match score (0-100) based on criteria above
2. What matches (3-5 specific points aligned with candidate strengths)
3. What doesn't match (2-4 concerns, red flags, or mismatches)
4. Key takeaways (2-3 critical points about fit and opportunity)

⚠️ REMEMBER: Fresh graduate with 485 visa = NO professional experience, NOT a citizen. Be STRICT about experience requirements.

Return ONLY valid JSON in this exact format:
{{{{
  "score": <integer 0-100 based on strict criteria above>,
  "matched": [
    "Specific match with candidate expertise",
    "Another alignment point",
    "Third matching aspect"
  ],
  "not_matched": [
    "Specific concern or red flag",
    "Gap or mismatch point"
  ],
  "key_points": [
    "Critical insight about this role",
    "Important consideration"
  ]
}}}}"""


# Load prompt template at module initialization (will be dynamic)
PROMPT_TEMPLATE = build_dynamic_prompt_template()


class ScoringError(Exception):
    """Base exception for scoring errors"""
    pass


class RateLimitError(ScoringError):
    """Rate limit exceeded"""
    pass


class ModelUnavailableError(ScoringError):
    """Model is not available"""
    pass


def load_profile():
    """Load profile content from profile.txt"""
    profile_path = Path(__file__).parent.parent / 'profile.txt'
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content.strip()) < 100:
            logger.warning("Profile content is very short. Consider adding more details.")
        
        return content
    except FileNotFoundError:
        logger.error("profile.txt not found")
        raise ScoringError("profile.txt not found")


def build_prompt(job, profile_content):
    """Build scoring prompt from job and profile"""
    # Phase 4: Include requirement_text in the prompt for AI scoring
    job_description = job.get('description', 'No description available')
    requirement_text = job.get('requirement_text', '')
    
    # If requirements exist, combine them with extra weight
    if requirement_text:
        combined_text = f"{job_description}\n\n⚠️ REQUIREMENTS SECTION (CRITICAL - CHECK FOR DEALBREAKERS):\n{requirement_text}"
    else:
        combined_text = job_description
    
    return PROMPT_TEMPLATE.format(
        profile_content=profile_content,
        job_title=job.get('title', 'Unknown'),
        job_company=job.get('company', 'Unknown'),
        job_location=job.get('location', 'Unknown'),
        job_description=combined_text
    )


def call_openrouter(model, prompt, api_key, max_tokens=None):
    """
    Call OpenRouter API with specified model
    Returns: response content dict
    """
    ai_config = _SCORER_CONFIG.get('ai', {})
    if max_tokens is None:
        max_tokens = ai_config.get('max_tokens', 500)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/job-scraper",
        "X-Title": "Job Scraper"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": max_tokens,
        "temperature": ai_config.get('temperature', 0.3)  # Load from config
    }
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Check for rate limiting
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        
        # Check for model availability
        if response.status_code == 400:
            error_msg = response.json().get('error', {}).get('message', '')
            if 'model' in error_msg.lower() or 'not found' in error_msg.lower():
                raise ModelUnavailableError(f"Model unavailable: {error_msg}")
        
        response.raise_for_status()
        
        data = response.json()
        
        # Extract content from response
        content = data['choices'][0]['message']['content']
        
        return content
        
    except requests.exceptions.Timeout:
        raise ScoringError("API request timed out")
    except requests.exceptions.RequestException as e:
        raise ScoringError(f"API request failed: {e}")


def parse_score_response(response_content):
    """Parse JSON response from AI model"""
    try:
        # Try to parse as JSON
        result = json.loads(response_content)
        
        # Validate structure
        if 'score' not in result:
            raise ValueError("Response missing score field")
        
        # Validate score range
        score = int(result['score'])
        if not 0 <= score <= 100:
            raise ValueError(f"Score out of range: {score}")
        
        # Handle both old and new format
        if 'reasoning' in result:
            # Old format - convert to new format
            return {
                'score': score,
                'reasoning': result['reasoning'],
                'matched': [],
                'not_matched': [],
                'key_points': [result['reasoning']]
            }
        else:
            # New format with structured data
            return {
                'score': score,
                'reasoning': ' '.join(result.get('key_points', [])),
                'matched': result.get('matched', []),
                'not_matched': result.get('not_matched', []),
                'key_points': result.get('key_points', [])
            }
        
    except json.JSONDecodeError:
        # Try to extract score and reasoning from text
        logger.warning("Failed to parse JSON, attempting text extraction")
        
        # Look for score
        import re
        score_match = re.search(r'"score":\s*(\d+)', response_content)
        
        if score_match:
            score = int(score_match.group(1))
            
            # Try to extract lists - simplified approach
            matched = []
            not_matched = []
            key_points = []
            
            # Try to find array content
            matched_match = re.search(r'"matched":\s*\[(.*?)\]', response_content, re.DOTALL)
            if matched_match:
                # Extract quoted strings from array
                matched = re.findall(r'"([^"]+)"', matched_match.group(1))
            
            not_matched_match = re.search(r'"not_matched":\s*\[(.*?)\]', response_content, re.DOTALL)
            if not_matched_match:
                not_matched = re.findall(r'"([^"]+)"', not_matched_match.group(1))
            
            key_points_match = re.search(r'"key_points":\s*\[(.*?)\]', response_content, re.DOTALL)
            if key_points_match:
                key_points = re.findall(r'"([^"]+)"', key_points_match.group(1))
            
            return {
                'score': score,
                'reasoning': ' '.join(key_points),
                'matched': matched,
                'not_matched': not_matched,
                'key_points': key_points
            }
        
        # Fallback - look for old format
        reasoning_match = re.search(r'"reasoning":\s*"([^"]+)"', response_content)
        if score_match and reasoning_match:
            return {
                'score': int(score_match.group(1)),
                'reasoning': reasoning_match.group(1),
                'matched': [],
                'not_matched': [],
                'key_points': [reasoning_match.group(1)]
            }
        
        raise ScoringError("Failed to parse AI response")


def score_job_with_fallback(job, profile_content, models_config, api_key):
    """
    Score a job using AI with model fallback chain
    Returns: {score: int, reasoning: str, model_used: str}
    """
    model_chain = [models_config['primary']] + models_config['fallbacks']
    failed_models = []  # Track which models failed and why
    
    for model in model_chain:
        try:
            logger.info(f"Scoring with model: {model}")
            
            prompt = build_prompt(job, profile_content)
            response_content = call_openrouter(model, prompt, api_key)
            
            result = parse_score_response(response_content)
            result['model_used'] = model
            
            logger.info(f"✓ Scored: {job.get('title', 'Unknown')} - {result['score']}%")
            return result
            
        except RateLimitError as e:
            ai_config = _SCORER_CONFIG.get('ai', {})
            retry_delay = ai_config.get('rate_limit_retry_delay', 3600)
            logger.warning(f"Rate limit hit for {model}, waiting {retry_delay}s...")
            # Pause then retry same model
            time.sleep(retry_delay)
            
            # Retry this model after waiting
            try:
                prompt = build_prompt(job, profile_content)
                response_content = call_openrouter(model, prompt, api_key)
                result = parse_score_response(response_content)
                result['model_used'] = model
                logger.info(f"✓ Scored after retry: {job.get('title', 'Unknown')} - {result['score']}%")
                return result
            except Exception as retry_error:
                logger.error(f"Retry failed for {model}: {retry_error}")
                continue
                
        except ModelUnavailableError as e:
            failed_models.append((model, f"Unavailable: {e}"))
            logger.warning(f"Model {model} unavailable, trying fallback: {e}")
            continue
            
        except ScoringError as e:
            failed_models.append((model, f"Error: {e}"))
            logger.error(f"Scoring error with {model}: {e}")
            continue
            
        except Exception as e:
            failed_models.append((model, f"Exception: {e}"))
            logger.error(f"Unexpected error with {model}: {e}")
            continue
    
    # All models failed - provide detailed summary
    failure_summary = "\n".join([f"  - {m}: {reason}" for m, reason in failed_models])
    logger.error(f"❌ ALL AI MODELS FAILED ({len(failed_models)} models tried):\n{failure_summary}")
    raise ScoringError(f"All {len(failed_models)} AI models failed to score job")


def score_batch(jobs, profile_content, models_config, api_key):
    """
    Score a batch of jobs with hard dealbreaker filtering
    Returns: {scored: int, failed: int, avg_score: float, scores: list}
    """
    scored = 0
    failed = 0
    rejected_by_parser = 0
    total_score = 0
    scores = []
    
    # Initialize parser if available
    parser = JobDescriptionParser() if PARSER_AVAILABLE else None
    
    logger.info(f"Starting batch scoring of {len(jobs)} jobs")
    if parser:
        logger.info("Parser enabled - enforcing hard dealbreaker filters")
    
    for i, job in enumerate(jobs, 1):
        try:
            logger.info(f"Scoring job {i}/{len(jobs)}: {job.get('title', 'Unknown')}")
            
            # HARD FILTER: Pre-check for dealbreakers using parser
            if parser:
                # Phase 4: Check BOTH description and requirements section
                description = job.get('description', '')
                requirement_text = job.get('requirement_text', '')
                
                # Combine for comprehensive check, with requirements weighted higher
                full_text = description
                if requirement_text:
                    # Prepend requirements to give them priority in parsing
                    full_text = f"REQUIREMENTS:\n{requirement_text}\n\nDESCRIPTION:\n{description}"
                
                parsed = parser.parse(
                    full_text,
                    job.get('title', ''),
                    job.get('location', '')
                )
                
                # If dealbreakers found, force score to 15-25 and skip AI scoring
                if parsed['dealbreakers']['has_dealbreakers']:
                    reasons = parsed['dealbreakers']['reasons']
                    
                    # Extract evidence snippets to show what triggered rejection
                    evidence = []
                    full_text_lower = full_text.lower()
                    
                    for reason in reasons:
                        if 'Senior' in reason or 'Lead' in reason:
                            # Find the actual text mentioning senior/lead
                            import re
                            senior_match = re.search(r'\b(senior|lead|principal|staff|architect)\s+\w+', full_text_lower)
                            if senior_match:
                                evidence.append(f"Found: '{senior_match.group(0)}' in description")
                        elif 'years' in reason:
                            # Find the years requirement
                            years_match = re.search(r'(\d+)\+?\s*years?', full_text_lower)
                            if years_match:
                                evidence.append(f"Found: '{years_match.group(0)}' requirement")
                        elif 'PR' in reason or 'Citizenship' in reason:
                            # Find citizenship/PR mention
                            pr_match = re.search(r'(australian\s+citizen|pr\s+required|security\s+clearance)', full_text_lower)
                            if pr_match:
                                evidence.append(f"Found: '{pr_match.group(0)}'")
                    
                    logger.warning(f"❌ PARSER REJECTION: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                    logger.warning(f"   Dealbreakers: {', '.join(reasons)}")
                    if evidence:
                        logger.warning(f"   Evidence: {' | '.join(evidence)}")
                    
                    # Add evidence to reasons for database storage
                    if evidence:
                        reasons.append(f"Evidence: {'; '.join(evidence)}")
                    
                    scores.append({
                        'job_id': job.get('id'),
                        'score': 20,  # Auto-reject score
                        'reasoning': f"AUTO-REJECTED: {', '.join(reasons)}",
                        'matched': [],
                        'not_matched': reasons,
                        'key_points': [f"Not suitable for fresh graduate with 485 visa"],
                        'model_used': 'parser-filter'
                    })
                    
                    rejected_by_parser += 1
                    scored += 1
                    total_score += 20
                    ai_config = _SCORER_CONFIG.get('ai', {})
                    time.sleep(ai_config.get('batch_delay', 0.1))  # Minimal delay
                    continue
            
            # Job passed parser check - proceed with AI scoring
            result = score_job_with_fallback(job, profile_content, models_config, api_key)
            
            # HARD FILTER: Post-AI validation for experience years in AI response
            final_score = result['score']
            final_reasoning = result['reasoning']
            final_not_matched = result.get('not_matched', [])
            
            # Override high scores if dealbreakers detected in AI's own analysis
            if final_score >= 70:
                reasoning_lower = final_reasoning.lower()
                not_matched_text = ' '.join(final_not_matched).lower()
                
                # Check if AI itself mentioned experience dealbreakers
                if any(pattern in reasoning_lower or pattern in not_matched_text for pattern in [
                    '5+ years', '5 years', '3+ years', '4+ years', '4 years',
                    'citizen', 'citizenship', 'pr required', 'security clearance',
                    'senior level', 'senior role', 'senior position'
                ]):
                    logger.warning(f"⚠️  OVERRIDING score from {final_score}% to 25% due to dealbreakers in AI analysis")
                    final_score = 25
                    final_reasoning = f"AUTO-OVERRIDE: {final_reasoning} [Score reduced due to dealbreakers]"
            
            scores.append({
                'job_id': job.get('id'),
                'score': final_score,
                'reasoning': final_reasoning,
                'matched': result.get('matched', []),
                'not_matched': final_not_matched,
                'key_points': result.get('key_points', []),
                'model_used': result['model_used']
            })
            
            scored += 1
            total_score += final_score
            
            # Rate limiting between jobs
            ai_config = _SCORER_CONFIG.get('ai', {})
            time.sleep(ai_config.get('score_retry_delay', 1))
            
        except ScoringError as e:
            logger.error(f"Failed to score job {job.get('title', 'Unknown')}: {e}")
            failed += 1
            continue
        except Exception as e:
            logger.error(f"Unexpected error scoring job: {e}")
            failed += 1
            continue
    
    avg_score = round(total_score / scored, 1) if scored > 0 else 0
    
    # Check if primary model was never used successfully
    models_config = _SCORER_CONFIG.get('ai', {}).get('models', {})
    primary_model = models_config.get('primary', 'unknown')
    models_used = set(s.get('model_used', '') for s in scores if s.get('model_used'))
    
    if primary_model and primary_model not in models_used and scored > 0:
        logger.warning(f"⚠️  PRIMARY MODEL NEVER SUCCEEDED: '{primary_model}' failed for all jobs. Used fallbacks: {', '.join(models_used)}")
    
    summary = {
        'processed': scored,  # Total jobs processed (includes AI scored + parser rejected)
        'ai_scored': scored - rejected_by_parser,  # Jobs that got numeric scores from AI
        'parser_rejected': rejected_by_parser,  # Jobs rejected before AI scoring
        'failed': failed,
        'avg_score': avg_score,
        'scores': scores
    }
    
    if parser:
        logger.info(f"Batch scoring complete: {scored - rejected_by_parser} AI scored, {rejected_by_parser} parser rejected, {failed} failed, avg: {avg_score}%")
    else:
        logger.info(f"Batch scoring complete: {scored} AI scored, {failed} failed, avg: {avg_score}%")
    
    return summary
