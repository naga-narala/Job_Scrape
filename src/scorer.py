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
    """Build component-based weighted scoring prompt template"""
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

    # Return component-based scoring template
    template = """You are an expert job matching system. Your task is to analyze a job posting and score it against a candidate profile using component-based weighted scoring.

===== CANDIDATE CONTEXT =====

PROFILE (What the candidate HAS):
{{profile_content}}

TARGET ROLES (What the candidate WANTS):
{{jobs_txt_content}}

===== JOB POSTING =====

Title: {{job_title}}
Company: {{job_company}}
Location: {{job_location}}
Description:
{{job_description}}

===== YOUR TASK =====

STEP 1: Extract all scoreable components from the job description.
Identify components in these categories:
- Technical Requirements (skills, tools, languages, frameworks)
- Experience Requirements (years, level, seniority)
- Education Requirements (degree, certifications)
- Location Requirements (remote, onsite, city, visa/immigration)
- Soft Skills (communication, leadership, teamwork)
- Company Benefits (salary, culture, growth opportunities)

STEP 2: For EACH component, determine:
a) Does the candidate profile satisfy this requirement? (yes/partial/no)
b) How critical is this component? (dealbreaker/important/preferred/nice_to_have)
c) What weight should it have? (Total across all components must sum to 100)

CRITICAL WEIGHTING RULES:
- "MUST have", "Required", "Essential" = dealbreaker
- "Preferred", "Desirable", "Plus" = nice_to_have
- Visa/citizenship requirements = dealbreaker if candidate cannot satisfy
- Years of experience significantly exceeding candidate level = dealbreaker
- Technical skills mentioned multiple times = higher weight
- Skills in job title = higher weight than skills in description

STEP 3: Calculate weighted score:
- If ANY dealbreaker component is NOT satisfied → final_score = 0-20%
- Each satisfied component contributes its weight to final score
- Partial satisfaction contributes 50% of component weight
- Components not satisfied contribute 0%

STEP 4: Return ONLY valid JSON (no markdown, no explanation):

{{
  "components": [
    {{
      "name": "Component Name",
      "category": "technical_requirements",
      "match_status": "yes",
      "criticality": "important",
      "weight": 15,
      "reasoning": "Brief explanation of match"
    }}
  ],
  "final_score": 75,
  "score_breakdown": {{
    "total_possible": 100,
    "earned": 75,
    "lost_to_dealbreakers": 0,
    "lost_to_gaps": 25
  }},
  "recommendation": "APPLY"
}}

IMPORTANT:
- Weights must sum to exactly 100
- match_status must be: "yes", "partial", or "no"
- criticality must be: "dealbreaker", "important", "preferred", or "nice_to_have"
- recommendation must be: "APPLY" (70-100%), "REVIEW" (40-69%), or "SKIP" (0-39%)
- Return ONLY the JSON, no other text
"""

    return template


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
    """Parse JSON response from AI model with component extraction (v3.0 - Hireability)"""
    
    # Clean response content - remove markdown code blocks if present
    content_clean = response_content.strip()
    if content_clean.startswith('```'):
        # Remove ```json and ``` markers
        import re
        content_clean = re.sub(r'^```(?:json)?\s*', '', content_clean)
        content_clean = re.sub(r'\s*```$', '', content_clean)
        content_clean = content_clean.strip()
    
    try:
        # Try to parse as JSON
        result = json.loads(content_clean)
        
        # Validate structure for hireability format
        if 'components' in result and 'score_breakdown' in result:
            # New hireability format with components
            components = result.get('components', [])
            final_score = result.get('score_breakdown', {}).get('final_score', 0)
            
            # Validate score
            if not 0 <= final_score <= 100:
                raise ValueError(f"Score out of range: {final_score}")
            
            # Extract matched/not_matched from components with safe access
            matched = []
            partial = []
            not_matched = []
            
            for c in components:
                if not isinstance(c, dict):
                    continue
                label = c.get('label', 'Unknown')
                status = c.get('status', 'unknown')
                
                if status == 'match':
                    matched.append(label)
                elif status == 'partial':
                    partial.append(label)
                elif status == 'miss':
                    not_matched.append(label)
                elif status == 'concern':
                    not_matched.append(label)  # Treat concerns as not matched
            
            # Combine partial with not_matched for concerns
            concerns = partial + not_matched
            
            # Build reasoning from explanation
            reasoning = result.get('explanation', '')
            if not reasoning:
                reasoning = f"{result.get('recommendation', 'UNKNOWN')}: {len(matched)} matches, {len(concerns)} concerns"
            
            # Extract risk profile and hard gate failure
            response_data = {
                'score': final_score,
                'reasoning': reasoning,
                'matched': matched,
                'not_matched': concerns,
                'key_points': components  # Store full component structure in key_points
            }
            
            # Add risk profile if present
            risk_profile = result.get('risk_profile')
            if risk_profile:
                response_data['risk_profile'] = risk_profile
            
            # Add hard gate failure if present
            hard_gate_failed = result.get('hard_gate_failed')
            if hard_gate_failed:
                response_data['hard_gate_failed'] = hard_gate_failed
            
            return response_data
        
        # Handle old format for backward compatibility
        if 'score' not in result:
            raise ValueError("Response missing score field")
        
        score = int(result['score'])
        if not 0 <= score <= 100:
            raise ValueError(f"Score out of range: {score}")
        
        # Old format handling
        if 'reasoning' in result:
            return {
                'score': score,
                'reasoning': result['reasoning'],
                'matched': [],
                'not_matched': [],
                'key_points': [result['reasoning']]
            }
        else:
            return {
                'score': score,
                'reasoning': ' '.join(result.get('key_points', [])),
                'matched': result.get('matched', []),
                'not_matched': result.get('not_matched', []),
                'key_points': result.get('key_points', [])
            }
        
    except json.JSONDecodeError:
        # Enhanced regex fallback for component extraction
        logger.warning("Failed to parse JSON, attempting component extraction from text")
        
        import re
        
        # Try to extract components array
        components_match = re.search(r'"components":\s*\[(.*?)\]', response_content, re.DOTALL)
        if components_match:
            components_text = components_match.group(1)
            
            # Extract component objects
            component_pattern = r'\{\s*"label":\s*"([^"]+)"\s*,\s*"score":\s*(\d+)\s*,\s*"status":\s*"([^"]+)"\s*\}'
            components = []
            for match in re.finditer(component_pattern, components_text):
                components.append({
                    'label': match.group(1),
                    'score': int(match.group(2)),
                    'status': match.group(3)
                })
            
            # Extract final score
            score_match = re.search(r'"final_score":\s*(\d+)', response_content)
            final_score = int(score_match.group(1)) if score_match else sum(c['score'] for c in components)
            
            # Extract explanation
            explanation_match = re.search(r'"explanation":\s*"([^"]+)"', response_content)
            explanation = explanation_match.group(1) if explanation_match else "Component-based scoring"
            
            # Build response
            matched = [c['label'] for c in components if c.get('status') == 'match']
            concerns = [c['label'] for c in components if c.get('status') in ['partial', 'miss']]
            
            return {
                'score': final_score,
                'reasoning': explanation,
                'matched': matched,
                'not_matched': concerns,
                'key_points': components
            }
        
        # Ultimate fallback - old format extraction
        score_match = re.search(r'"score":\s*(\d+)', response_content)
        if score_match:
            score = int(score_match.group(1))
            
            matched = []
            not_matched = []
            key_points = []
            
            matched_match = re.search(r'"matched":\s*\[(.*?)\]', response_content, re.DOTALL)
            if matched_match:
                matched = re.findall(r'"([^"]+)"', matched_match.group(1))
            
            not_matched_match = re.search(r'"not_matched":\s*\[(.*?)\]', response_content, re.DOTALL)
            if not_matched_match:
                not_matched = re.findall(r'"([^"]+)"', not_matched_match.group(1))
            
            key_points_match = re.search(r'"key_points":\s*\[(.*?)\]', response_content, re.DOTALL)
            if key_points_match:
                key_points = re.findall(r'"([^"]+)"', key_points_match.group(1))
            
            return {
                'score': score,
                'reasoning': ' '.join(key_points) if key_points else 'Fallback parsing',
                'matched': matched,
                'not_matched': not_matched,
                'key_points': key_points if key_points else []
            }
        
        # Absolute fallback - return minimal valid structure
        logger.error("Could not parse any recognizable scoring format")
        return {
            'score': 0,
            'reasoning': 'ERROR: Could not parse AI response',
            'matched': [],
            'not_matched': ['Parsing failed'],
            'key_points': []
        }


def score_job_with_fallback(job, profile_content, models_config, api_key):
    """
    Score a job using AI with model fallback chain
    Returns: {score: int, reasoning: str, model_used: str, risk_profile: dict, hard_gate_failed: str|None}
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
            
            # Extract risk profile from result if available
            risk_profile = result.get('risk_profile', {})
            if risk_profile:
                result['risk_profile'] = risk_profile
                logger.debug(f"Extracted risk profile: {risk_profile}")
            
            # Handle hard gate failures
            hard_gate_failed = result.get('hard_gate_failed')
            if hard_gate_failed:
                logger.warning(f"Hard gate failed for {job.get('title', 'Unknown')}: {hard_gate_failed}")
                result['hard_gate_failed'] = hard_gate_failed
                result['score'] = 0  # Override score for hard gate failures
                result['recommendation'] = 'SKIP'
            
            # Map component statuses correctly
            components = result.get('key_points', [])
            if components and isinstance(components, list):
                # Ensure all components have proper status values
                for comp in components:
                    if isinstance(comp, dict):
                        status = comp.get('status', 'unknown')
                        # Normalize status values
                        if status not in ['match', 'partial', 'miss', 'concern']:
                            if status == 'yes':
                                comp['status'] = 'match'
                            elif status == 'no':
                                comp['status'] = 'miss'
                            else:
                                comp['status'] = 'partial'  # Default to partial for unknown
            
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
                
                # Extract risk profile from retry result
                risk_profile = result.get('risk_profile', {})
                if risk_profile:
                    result['risk_profile'] = risk_profile
                
                # Handle hard gate failures in retry
                hard_gate_failed = result.get('hard_gate_failed')
                if hard_gate_failed:
                    result['hard_gate_failed'] = hard_gate_failed
                    result['score'] = 0
                    result['recommendation'] = 'SKIP'
                
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
