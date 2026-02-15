"""
Job Scorer - Hybrid Scoring System Wrapper

This module provides backward-compatible interface to the new hybrid scoring system.
Legacy scoring code has been completely removed and replaced with hybrid scorer.

The hybrid system combines:
- Component-based scoring (technical requirements, weights)
- Hireability-based scoring (legal/visa, experience, recruiter, skill, narrative)
- Risk profiling
- Hard gate checks

All in a single AI call for cost efficiency.

Author: AI Agent
Updated: 2026-02-14
"""

import logging
from pathlib import Path

# Import hybrid scorer
from hybrid_scorer import (
    score_job_hybrid,
    score_job_with_fallback as _hybrid_score_with_fallback,
    score_batch_hybrid,
    load_profile as _hybrid_load_profile,
    load_jobs_txt
)

logger = logging.getLogger(__name__)


def load_profile():
    """
    Load candidate profile from profile.txt
    
    Returns:
        str: Profile content
    """
    return _hybrid_load_profile()


def score_job_with_fallback(job, profile_content, models_config, api_key):
    """
    Score a single job using hybrid scoring with model fallback
    
    This is a backward-compatible wrapper for the hybrid scoring system.
    
    Args:
        job: Job dict with title, company, location, description
        profile_content: Candidate profile text
        models_config: Dict with 'primary' and 'fallbacks' list
        api_key: OpenRouter API key
    
    Returns:
        dict: Scoring result with hybrid fields
            - score: Final score (0-100)
            - reasoning: Explanation text
            - model_used: Model that succeeded
            - components: List of component dicts
            - score_breakdown: Score breakdown dict
            - hireability_factors: Hireability scores dict
            - risk_profile: Risk assessment dict
            - recommendation: APPLY/CLARIFY/SKIP
            - hard_gate_failed: Reason if failed, else null
            - scoring_method: 'hybrid'
    """
    # Load jobs.txt for context
    jobs_txt_content = load_jobs_txt()
    
    # Call hybrid scorer
    result = _hybrid_score_with_fallback(
        job,
        profile_content,
        jobs_txt_content,
        models_config,
        api_key
    )
    
    return result


def score_batch(jobs, profile_content, models_config, api_key):
    """
    Score a batch of jobs using hybrid scoring system
    
    This is a backward-compatible wrapper for the hybrid scoring system.
    
    Args:
        jobs: List of job dicts
        profile_content: Candidate profile text
        models_config: Dict with 'primary' and 'fallbacks' list
        api_key: OpenRouter API key
    
    Returns:
        dict: Summary with:
            - processed: Number of jobs processed
            - ai_scored: Number successfully scored
            - parser_rejected: Number rejected (0 in hybrid, handled by hard gates)
            - failed: Number that failed
            - avg_score: Average score
            - scores: List of score results
    """
    # Load jobs.txt for context
    jobs_txt_content = load_jobs_txt()
    
    # Call hybrid batch scorer
    summary = score_batch_hybrid(
        jobs,
        profile_content,
        jobs_txt_content,
        models_config,
        api_key
    )
    
    return summary


# Legacy functions removed:
# - build_dynamic_prompt_template() -> Now in hybrid_scorer
# - load_keywords() -> Not needed in hybrid
# - load_jobs_txt_metadata() -> Integrated into hybrid prompt
# - build_prompt() -> Now in hybrid_scorer
# - call_openrouter() -> Now in hybrid_scorer
# - parse_score_response() -> Now in hybrid_scorer

# Note: JobDescriptionParser is no longer used
# Hard gate checks are now handled by the AI in the hybrid prompt
# This provides more nuanced and context-aware filtering
