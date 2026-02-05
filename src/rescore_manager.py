import logging
from pathlib import Path
import database as db
import scorer

logger = logging.getLogger(__name__)


def detect_profile_change():
    """
    Detect if profile.txt has changed since last run
    Returns: True if changed, False otherwise
    """
    current_hash = db.get_profile_hash()
    
    if not current_hash:
        logger.warning("Could not calculate profile hash")
        return False
    
    last_hash = db.get_last_profile_hash()
    
    if last_hash is None:
        # First run, record current hash
        db.insert_profile_change(current_hash)
        logger.info("First run: Profile hash recorded")
        return False
    
    if current_hash != last_hash:
        logger.info("Profile change detected!")
        db.insert_profile_change(current_hash)
        return True
    
    logger.info("Profile unchanged")
    return False


def trigger_smart_rescore(profile_content, config):
    """
    Re-score jobs that:
    - Scored between threshold_min and threshold_max
    - Are less than max_age_days old
    - Were scored with different profile hash
    
    Returns: number of jobs rescored
    """
    current_hash = db.get_profile_hash()
    
    if not current_hash:
        logger.error("Cannot rescore: profile hash unavailable")
        return 0
    
    # Get configuration
    min_score = config.get('rescore_threshold_min', 70)
    max_score = config.get('rescore_threshold_max', 79)
    max_age_days = config.get('rescore_max_age_days', 7)
    
    logger.info(f"Smart rescore: looking for jobs {min_score}-{max_score}%, <{max_age_days} days old")
    
    # Get eligible jobs
    jobs_to_rescore = db.get_jobs_for_rescore(
        min_score=min_score,
        max_score=max_score,
        max_age_days=max_age_days,
        exclude_profile_hash=current_hash
    )
    
    if not jobs_to_rescore:
        logger.info("No jobs eligible for rescoring")
        return 0
    
    logger.info(f"Found {len(jobs_to_rescore)} jobs eligible for rescoring")
    
    rescored_count = 0
    upgraded_count = 0
    
    models_config = config.get('ai_models', {})
    api_key = config.get('openrouter_api_key')
    
    for job in jobs_to_rescore:
        try:
            old_score = job.get('old_score', 0)
            
            logger.info(f"Re-scoring: {job['title']} (was {old_score}%)")
            
            # Score with current profile
            score_result = scorer.score_job_with_fallback(
                job, 
                profile_content, 
                models_config, 
                api_key
            )
            
            # Delete old score
            db.delete_score(job['id'])
            
            # Insert new score
            db.insert_score(job['id'], score_result, current_hash)
            
            new_score = score_result['score']
            rescored_count += 1
            
            # Check if upgraded to high-confidence match
            threshold = config.get('match_threshold', 75)
            if old_score < threshold and new_score >= threshold:
                upgraded_count += 1
                logger.info(f"✓ Upgraded: {job['title']} - {old_score}% → {new_score}%")
            else:
                logger.info(f"Re-scored: {job['title']} - {old_score}% → {new_score}%")
            
        except Exception as e:
            logger.error(f"Failed to rescore job {job.get('title', 'Unknown')}: {e}")
            continue
    
    logger.info(f"Smart rescore complete: {rescored_count} rescored, {upgraded_count} upgraded to {threshold}%+")
    
    return rescored_count
