"""
Hybrid Job Scoring System - Component + Hireability Combined

Combines component-based scoring and hireability-based scoring in a single AI call
to save API costs while providing comprehensive job analysis.

Features:
- Hard gate checks (citizenship, experience, clearance)
- Component extraction with weights
- Hireability factors (legal/visa, experience, recruiter, skill, narrative)
- Risk profiling
- Single API call (cost-efficient)

Author: AI Agent
Created: 2026-02-14
"""

import requests
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Load config at module level
_config_path = Path(__file__).parent.parent / 'config.json'
with open(_config_path, 'r') as f:
    _CONFIG = json.load(f)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_profile():
    """Load candidate profile from profile.txt"""
    profile_path = Path(__file__).parent.parent / 'profile.txt'
    with open(profile_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_jobs_txt():
    """Load jobs.txt for context"""
    jobs_path = Path(__file__).parent.parent / 'jobs.txt'
    with open(jobs_path, 'r', encoding='utf-8') as f:
        return f.read()


# HYBRID SCORING PROMPT - Combines both approaches
HYBRID_SCORING_PROMPT = """You are an expert hybrid job matching engine that combines component analysis with hireability assessment.

═══════════════════════════════════════════════════════════════════
📂 CANDIDATE CONTEXT
═══════════════════════════════════════════════════════════════════

PROFILE (What candidate HAS):
{profile_content}

TARGET ROLES (What candidate WANTS):
{jobs_txt_content}

═══════════════════════════════════════════════════════════════════
📋 JOB POSTING TO ANALYZE
═══════════════════════════════════════════════════════════════════

Title: {job_title}
Company: {job_company}
Location: {job_location}

Description:
{job_description}

═══════════════════════════════════════════════════════════════════
🔍 STEP 1: HARD GATE CHECKS (Binary Pass/Fail)
═══════════════════════════════════════════════════════════════════

Check these dealbreakers STRICTLY. If ANY fail → STOP and return score=0.

❌ Citizenship/PR Required
  - "Australian citizen", "PR required", "must hold citizenship"
  - Candidate has 485 visa (temporary graduate visa) - NOT a citizen/PR
  - FAIL only if explicitly required

❌ Security Clearance Required
  - "NV1", "NV2", "baseline clearance"
  - Candidate is NOT Australian citizen → cannot get clearance
  - FAIL only if explicitly required

❌ No Visa Sponsorship + Candidate Needs It
  - "No visa sponsorship", "must have permanent work rights"
  - Candidate has 485 visa with FULL current work rights
  - FAIL only if "no sponsorship" AND 485 expires soon

❌ Licensed Profession Required
  - Medicine, Law, Civil/Mining Engineering, Nursing, Teaching
  - Candidate has AI/Data Science degree → cannot practice
  - FAIL only if licensed profession required

❌ Minimum Experience Not Met (CRITICAL)
  - "3+ years", "5+ years", Senior/Lead/Principal title
  - Candidate is FRESH GRADUATE (ZERO commercial experience)
  - FAIL if requires 3+ years OR Senior/Lead/Principal title

❌ Geographic Impossibility
  - Role in overseas location AND candidate states Australia-only
  - FAIL only if truly impossible

⚠️ If ANY hard gate fails → Return immediately:
{{
  "hard_gate_failed": "<specific reason>",
  "final_score": 0,
  "recommendation": "SKIP",
  "explanation": "Application impossible: <reason>"
}}

═══════════════════════════════════════════════════════════════════
🧩 STEP 2: COMPONENT EXTRACTION & WEIGHTED SCORING
═══════════════════════════════════════════════════════════════════

If hard gates passed, extract ALL scoreable components:

Categories:
- technical_requirements (skills, tools, languages, frameworks)
- experience_requirements (years, level, seniority)
- education_requirements (degree, certifications)
- location_requirements (remote, onsite, city, visa)
- soft_skills (communication, teamwork, leadership)
- benefits_compensation (salary, culture, growth)

For EACH component:
1. Does candidate satisfy? (yes/partial/no)
2. How critical? (dealbreaker/important/preferred/nice_to_have)
3. Weight? (total must sum to 100)

Weighting Rules:
- "MUST", "Required", "Essential" = dealbreaker (high weight)
- Skills in job TITLE = higher weight
- Skills mentioned multiple times = higher weight
- "Preferred", "Plus", "Nice to have" = nice_to_have (lower weight)

Calculate component_score:
- Satisfied component contributes full weight
- Partial contributes 50% of weight
- Not satisfied contributes 0%

═══════════════════════════════════════════════════════════════════
📊 STEP 3: HIREABILITY FACTORS SCORING
═══════════════════════════════════════════════════════════════════

Score these 5 factors (predict REAL interview probability):

🛂 Legal & Visa Compatibility (0-25 points)
  25: Australian citizen/PR, no friction
  20: 485 visa + no sponsorship needed + non-government
  15: 485 visa + sponsorship available
  10: 485 visa + unclear sponsorship
  5: Visa renewal soon + no clarity
  0: Hard gate failed

💼 Experience Credibility (0-25 points)
  25: Graduate/Junior + candidate is fresh grad (PERFECT)
  20: 0-2 years + strong academic projects
  15: Undefined level + transferable skills
  10: Mid-level + exceptional portfolio
  5: 2-3 years + fresh grad (STRETCH)
  0: 3+ years/Senior + fresh grad (IMPOSSIBLE)

👁️ Recruiter Comprehension (0-15 points)
  15: Job title + background = obvious match
  12: Technical match clear, recruiter needs to read
  9: Match exists but requires interpretation
  6: Recruiter confused by title
  3: Recruiter likely skips based on title
  0: Completely irrelevant

💰 Skill Monetization (0-15 points)
  15: Perfect technical alignment
  12: Strong core + minor gaps
  9: Adequate fit, missing 1-2 technologies
  6: Partial fit, significant gaps
  3: Minimal overlap
  0: No relevant skills

📖 Narrative Coherence (0-10 points)
  10: Natural career progression
  8: Logical lateral move
  6: Explainable pivot
  4: Questionable but defensible
  2: Confusing, needs explanation
  0: Makes no sense

Calculate hireability_score = sum of all 5 factors (max 90)

═══════════════════════════════════════════════════════════════════
🎯 STEP 4: RISK PROFILING
═══════════════════════════════════════════════════════════════════

Classify these factors:

Role Level Risk: LOW / MEDIUM / HIGH / EXTREME
Employer Type: Startup / SME / Enterprise / Bank / Government
Visa Friction Level: LOW / MEDIUM / HIGH / FATAL
Experience Stretch: PERFECT / MODERATE / SEVERE / FATAL

═══════════════════════════════════════════════════════════════════
🧮 STEP 5: CALCULATE FINAL SCORE
═══════════════════════════════════════════════════════════════════

Blend both scores for final result:
final_score = (component_score * 0.6) + (hireability_score * 0.4)

This balances technical fit (60%) with real-world hireability (40%).

═══════════════════════════════════════════════════════════════════
🎬 STEP 6: MAKE RECOMMENDATION
═══════════════════════════════════════════════════════════════════

Based on final_score:
- APPLY (≥70): Strong match, high probability
- CLARIFY (50-69): Borderline, reach out to recruiter first
- SKIP (<50): Low probability, time better spent elsewhere

═══════════════════════════════════════════════════════════════════
📤 OUTPUT FORMAT (Return ONLY valid JSON)
═══════════════════════════════════════════════════════════════════

{{
  "hard_gate_failed": null,
  "components": [
    {{
      "name": "Python",
      "category": "technical_requirements",
      "match_status": "yes",
      "criticality": "important",
      "weight": 15,
      "reasoning": "Candidate has 2 years Python experience"
    }}
  ],
  "score_breakdown": {{
    "component_score": 75,
    "hireability_score": 80,
    "final_score": 77,
    "total_possible": 100,
    "earned": 77,
    "lost_to_dealbreakers": 0,
    "lost_to_gaps": 23
  }},
  "hireability_factors": {{
    "legal_visa": 20,
    "experience_credibility": 25,
    "recruiter_comprehension": 12,
    "skill_monetization": 15,
    "narrative_coherence": 8
  }},
  "risk_profile": {{
    "role_level_risk": "LOW",
    "employer_type": "Startup",
    "visa_friction_level": "LOW",
    "experience_stretch": "PERFECT"
  }},
  "recommendation": "APPLY",
  "explanation": "2-3 sentence summary of key matches/gaps and reasoning for score",
  "model_used": "deepseek/deepseek-chat"
}}

═══════════════════════════════════════════════════════════════════
⚠️ CRITICAL REMINDERS
═══════════════════════════════════════════════════════════════════

✓ 485 visa holder ≠ citizen ≠ PR (temporary visa with full work rights)
✓ Fresh graduate = ZERO commercial experience (academic ≠ professional)
✓ Government roles are EXTREMELY conservative with visa holders
✓ "Preference for citizens" = soft rejection for 485 visa holders
✓ Component weights MUST sum to exactly 100
✓ Be STRICT on experience requirements (3+ years = dealbreaker)
✓ Return ONLY valid JSON, no markdown or extra text"""


def call_openrouter_hybrid(model, prompt, api_key, max_tokens=2000):
    """
    Call OpenRouter API with hybrid scoring prompt
    
    Args:
        model: Model ID (e.g., "deepseek/deepseek-chat")
        prompt: Formatted prompt
        api_key: OpenRouter API key
        max_tokens: Max tokens for response (default: 2000)
    
    Returns:
        dict: Parsed JSON response
        
    Raises:
        Exception: If API call or parsing fails
    """
    ai_config = _CONFIG.get('ai', {})
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/job-scraper",
        "X-Title": "Job Scraper Hybrid Scoring"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "max_tokens": max_tokens,
        "temperature": ai_config.get('temperature', 0.2)
    }
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # Parse JSON response
        result = json.loads(content)
        
        # Validate critical fields
        if 'hard_gate_failed' not in result:
            result['hard_gate_failed'] = None
        if 'recommendation' not in result:
            result['recommendation'] = 'CLARIFY'
        if 'explanation' not in result:
            result['explanation'] = 'No explanation provided'
        
        # Ensure score_breakdown exists
        if 'score_breakdown' not in result:
            # Try to construct it from other fields
            result['score_breakdown'] = {
                'component_score': result.get('component_score', 0),
                'hireability_score': result.get('hireability_score', 0),
                'final_score': result.get('final_score', result.get('score', 0)),
                'total_possible': 100,
                'earned': result.get('final_score', result.get('score', 0)),
                'lost_to_dealbreakers': 0,
                'lost_to_gaps': 100 - result.get('final_score', result.get('score', 0))
            }
        
        # Add model used to result
        result['model_used'] = model
        
        # Extract final score from breakdown
        if 'score_breakdown' in result and 'final_score' in result['score_breakdown']:
            result['score'] = result['score_breakdown']['final_score']
        else:
            # Fallback if score_breakdown doesn't have final_score
            result['score'] = result.get('score', 0)
        
        # Add reasoning field for backward compatibility
        result['reasoning'] = result.get('explanation', '')
        
        return result
        
    except requests.exceptions.Timeout:
        raise Exception("API request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        raise Exception(f"Hybrid scoring error: {e}")


def score_job_hybrid(job, profile_content, jobs_txt_content, model, api_key):
    """
    Score a job using hybrid scoring system
    
    Args:
        job: Job dict with title, company, location, description
        profile_content: Candidate profile text
        jobs_txt_content: Jobs.txt content
        model: AI model ID
        api_key: OpenRouter API key
    
    Returns:
        dict: Scoring result with all hybrid fields
    """
    # Build prompt
    prompt = HYBRID_SCORING_PROMPT.format(
        profile_content=profile_content,
        jobs_txt_content=jobs_txt_content,
        job_title=job.get('title', 'Unknown'),
        job_company=job.get('company', 'Unknown'),
        job_location=job.get('location', 'Unknown'),
        job_description=job.get('description', 'No description available')
    )
    
    # Call API
    result = call_openrouter_hybrid(model, prompt, api_key)
    
    # Set scoring method
    result['scoring_method'] = 'hybrid'
    
    logger.info(f"✓ Hybrid scored: {job.get('title', 'Unknown')} - {result['score']}%")
    
    return result


def score_job_with_fallback(job, profile_content, jobs_txt_content, models_config, api_key):
    """
    Score a job with model fallback chain
    
    Args:
        job: Job dict
        profile_content: Candidate profile
        jobs_txt_content: Jobs.txt content
        models_config: Dict with 'primary' and 'fallbacks' list
        api_key: OpenRouter API key
    
    Returns:
        dict: Scoring result
        
    Raises:
        Exception: If all models fail
    """
    model_chain = [models_config['primary']] + models_config.get('fallbacks', [])
    failed_models = []
    
    for model in model_chain:
        try:
            logger.info(f"Attempting hybrid scoring with model: {model}")
            result = score_job_hybrid(job, profile_content, jobs_txt_content, model, api_key)
            logger.info(f"✓ Success with {model}")
            return result
            
        except Exception as e:
            failed_models.append((model, str(e)))
            logger.warning(f"Model {model} failed: {e}")
            continue
    
    # All models failed
    failure_summary = "\n".join([f"  - {m}: {reason}" for m, reason in failed_models])
    logger.error(f"❌ ALL MODELS FAILED ({len(failed_models)} tried):\n{failure_summary}")
    raise Exception(f"All {len(failed_models)} AI models failed to score job")


def score_batch_hybrid(jobs, profile_content, jobs_txt_content, models_config, api_key):
    """
    Score a batch of jobs using hybrid system
    
    Args:
        jobs: List of job dicts
        profile_content: Candidate profile
        jobs_txt_content: Jobs.txt content
        models_config: Models configuration
        api_key: OpenRouter API key
    
    Returns:
        dict: Summary with scored jobs and statistics
    """
    import time
    
    ai_config = _CONFIG.get('ai', {})
    scored = 0
    failed = 0
    total_score = 0
    scores = []
    
    logger.info(f"Starting hybrid batch scoring of {len(jobs)} jobs")
    
    for i, job in enumerate(jobs, 1):
        try:
            logger.info(f"Scoring job {i}/{len(jobs)}: {job.get('title', 'Unknown')}")
            
            result = score_job_with_fallback(
                job, profile_content, jobs_txt_content, models_config, api_key
            )
            
            result['job_id'] = job.get('id')
            scores.append(result)
            
            scored += 1
            total_score += result['score']
            
            # Rate limiting between jobs
            time.sleep(ai_config.get('score_retry_delay', 1))
            
        except Exception as e:
            logger.error(f"Failed to score job {job.get('title', 'Unknown')}: {e}")
            failed += 1
            continue
    
    avg_score = round(total_score / scored, 1) if scored > 0 else 0
    
    summary = {
        'processed': scored,
        'ai_scored': scored,  # All are AI scored in hybrid
        'parser_rejected': 0,  # No parser rejection in hybrid (handled by hard gates)
        'failed': failed,
        'avg_score': avg_score,
        'scores': scores
    }
    
    logger.info(f"Hybrid batch complete: {scored} scored, {failed} failed, avg: {avg_score}%")
    
    return summary
