#!/usr/bin/env python3
"""
Job Description Parser - Universal & Role-Agnostic

Dynamically adapts to ANY job role by loading keywords from generated_keywords.json
Extracts structured metadata from job descriptions with focus on:
- Auto-rejecting unsuitable roles based on user-configurable dealbreakers
- Identifying suitable opportunities based on target job titles
- Matching technical requirements against generated skill list
- Location and visa compatibility
"""

import re
import json
import logging
from typing import Dict, List, Set, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class JobDescriptionParser:
    """
    Universal job description parser that adapts to any role
    Loads keywords and dealbreakers from generated_keywords.json
    """
    
    def __init__(self, keywords_file: str = "generated_keywords.json"):
        """
        Initialize parser with keywords from generated file
        
        Args:
            keywords_file: Path to generated keywords JSON file
        """
        self.keywords_file = keywords_file
        self._load_keywords()
        self._compile_patterns()
    
    def _load_keywords(self):
        """Load keywords and configuration from generated_keywords.json"""
        try:
            with open(self.keywords_file, 'r') as f:
                data = json.load(f)
            
            # Load technical skills (from AI generation)
            self.PROFILE_SKILLS = set(skill.lower() for skill in data.get('technical_skills', []))
            
            # Load strong keywords (must-have terms)
            self.STRONG_KEYWORDS = set(kw.lower() for kw in data.get('strong_keywords', []))
            
            # Load dealbreakers from jobs.txt configuration
            dealbreakers = data.get('dealbreakers', {})
            self.max_experience = int(dealbreakers.get('max_experience', 2))
            self.exclude_seniority = [s.strip().lower() for s in dealbreakers.get('exclude_seniority', '').split(',') if s.strip()]
            self.exclude_visa = [v.strip().lower() for v in dealbreakers.get('exclude_visa', '').split(',') if v.strip()]
            self.exclude_education = [e.strip().lower() for e in dealbreakers.get('exclude_education', '').split(',') if e.strip()]
            
            # Load preferences
            preferences = data.get('preferences', {})
            locations_str = preferences.get('locations', 'Perth, Melbourne, Remote')
            self.preferred_locations = [loc.strip() for loc in locations_str.split(',') if loc.strip()]
            
            # Set location scores (prioritize first locations in list)
            self.LOCATION_SCORES = {}
            base_score = 100
            for loc in self.preferred_locations:
                self.LOCATION_SCORES[loc.lower()] = base_score
                base_score -= 10
            
            logger.info(f"Loaded keywords from {self.keywords_file}")
            logger.info(f"Technical skills: {len(self.PROFILE_SKILLS)}")
            logger.info(f"Max experience: {self.max_experience} years")
            logger.info(f"Excluded seniority levels: {len(self.exclude_seniority)}")
            
        except FileNotFoundError:
            logger.error(f"Keywords file not found: {self.keywords_file}")
            logger.warning("Using empty keyword sets - parser may not work correctly!")
            self.PROFILE_SKILLS = set()
            self.STRONG_KEYWORDS = set()
            self.max_experience = 2
            self.exclude_seniority = []
            self.exclude_visa = []
            self.exclude_education = []
            self.LOCATION_SCORES = {'perth': 100, 'melbourne': 90, 'remote': 80}
        except Exception as e:
            logger.error(f"Error loading keywords: {e}")
            raise
    
    def _compile_patterns(self):
        """Compile all regex patterns for performance (using dynamic dealbreakers)"""
        
        # Build PR/Citizenship pattern from user-configurable exclusions
        if self.exclude_visa:
            visa_terms = '|'.join(re.escape(term) for term in self.exclude_visa)
            pr_pattern = rf'\b({visa_terms})\b'
        else:
            pr_pattern = r'\b(australian\s+pr|citizenship\s+required|security\s+clearance)\b'
        
        # Build seniority pattern from user-configurable exclusions
        if self.exclude_seniority:
            seniority_terms = '|'.join(re.escape(term) for term in self.exclude_seniority)
            senior_pattern = rf'\b({seniority_terms})\b(?!.*\b(junior|graduate)\b)'
        else:
            senior_pattern = r'\b(senior|lead|principal|staff|manager|director)\b(?!.*\b(junior|graduate)\b)'
        
        # Build years pattern based on max_experience
        if self.max_experience >= 0:
            min_years = self.max_experience + 1  # If max is 2, reject 3+
            years_pattern = rf'\b([{min_years}-9]|1[0-9])\+?\s*years?\s*(of)?\s*(professional\s+)?experience\b'
        else:
            years_pattern = r'\b([5-9]|1[0-9])\+?\s*years?\s*experience\b'  # Default: reject 5+
        
        # Build education pattern from user-configurable exclusions
        if self.exclude_education:
            edu_terms = '|'.join(re.escape(term) for term in self.exclude_education)
            phd_pattern = rf'\b({edu_terms})\b'
        else:
            phd_pattern = r'\b(phd\s+required|doctorate\s+required)\b'
        
        # Dealbreaker patterns (dynamic based on user config)
        self.patterns = {
            'pr_citizenship': re.compile(pr_pattern, re.IGNORECASE),
            'senior_level': re.compile(senior_pattern, re.IGNORECASE),
            'years_excessive': re.compile(years_pattern, re.IGNORECASE),
            'phd_required': re.compile(phd_pattern, re.IGNORECASE),
            
            # Graduate-friendly signals (universal patterns)
            'explicit_graduate': re.compile(
                r'\b(graduate\s+program|grad\s+role|recent\s+graduate'
                r'|fresh\s+graduate|new\s+graduate|masters\s+graduate'
                r'|graduate\s+position|graduate\s+opportunity)\b',
                re.IGNORECASE
            ),
            
            'entry_level': re.compile(
                r'\b(entry[\s-]level|junior|associate|junior\s+level'
                r'|entry\s+level\s+position|early\s+career)\b',
                re.IGNORECASE
            ),
            
            'years_0_2': re.compile(
                r'\b([0-2]|1-2|0-1)\s*years?\s*(of)?\s*experience\b',
                re.IGNORECASE
            ),
            
            'masters_preferred': re.compile(
                r'\b(masters\s+degree|masters\s+in|msc|m\.s\.|masters\s+qualification'
                r'|postgraduate\s+degree|graduate\s+degree)\b',
                re.IGNORECASE
            ),
            
            # Technical domain patterns (will be supplemented by dynamic keywords)
            'machine_learning': re.compile(
                r'\b(machine\s+learning|ml\s+engineer|ml\s+model|supervised\s+learning'
                r'|unsupervised\s+learning|ml\s+models?)\b',
                re.IGNORECASE
            ),
            
            'deep_learning': re.compile(
                r'\b(deep\s+learning|neural\s+network|cnn|rnn|transformer'
                r'|dl\s+model|deep\s+neural)\b',
                re.IGNORECASE
            ),
            
            'computer_vision': re.compile(
                r'\b(computer\s+vision|cv|image\s+processing|object\s+detection'
                r'|yolo|opencv|image\s+segmentation|image\s+classification)\b',
                re.IGNORECASE
            ),
            
            'agentic_ai': re.compile(
                r'\b(langchain|crewai|multi[\s-]agent|agentic|autonomous\s+agent'
                r'|agent\s+orchestration|langgraph|ai\s+agent)\b',
                re.IGNORECASE
            ),
            
            'llm_rag': re.compile(
                r'\b(llm|large\s+language\s+model|rag|retrieval|vector\s+database'
                r'|embedding|prompt\s+engineering|gpt|claude)\b',
                re.IGNORECASE
            ),
            
            'mlops': re.compile(
                r'\b(mlops|ml[\s-]ops|model\s+deployment|model\s+serving'
                r'|mlflow|kubeflow|ci/cd\s+for\s+ml|model\s+monitoring)\b',
                re.IGNORECASE
            ),
            
            'data_science': re.compile(
                r'\b(data\s+scientist|data\s+science|statistical\s+analysis'
                r'|data\s+analytics)\b',
                re.IGNORECASE
            ),
            
            # Remote/location patterns
            'remote_full': re.compile(
                r'\b(fully\s+remote|100%\s+remote|remote[\s-]first'
                r'|work\s+from\s+home|wfh|remote\s+position)\b',
                re.IGNORECASE
            ),
            
            'hybrid': re.compile(
                r'\b(hybrid|(\d+)\s*days?\s*(in[\s-]office|onsite|office))\b',
                re.IGNORECASE
            ),
            
            'visa_sponsorship': re.compile(
                r'\b(visa\s+sponsorship|485\s+visa|sponsor\s+visa'
                r'|sponsorship\s+available|will\s+sponsor)\b',
                re.IGNORECASE
            ),
            
            # Company/culture signals
            'mentorship': re.compile(
                r'\b(mentorship|mentor|coaching|learning\s+opportunities'
                r'|professional\s+development|training\s+program)\b',
                re.IGNORECASE
            ),
            
            'growth': re.compile(
                r'\b(career\s+growth|progression|advancement|learning\s+path'
                r'|development\s+opportunities)\b',
                re.IGNORECASE
            ),
        }
    
    def parse(self, job_description: str, job_title: str = "", location: str = "") -> Dict:
        """
        Parse job description and return structured metadata
        
        Args:
            job_description: Full job description text
            job_title: Job title (optional, helps with context)
            location: Job location (optional)
        
        Returns:
            Structured dictionary with parsing results
        """
        if not job_description:
            return self._empty_result("No description provided")
        
        desc_lower = job_description.lower()
        title_lower = job_title.lower()
        
        # Stage 1: Check dealbreakers first
        dealbreakers = self._check_dealbreakers(desc_lower, title_lower)
        
        # Stage 2: Extract graduate signals
        graduate_signals = self._extract_graduate_signals(desc_lower, title_lower)
        
        # Stage 3: AI/ML domain detection
        ai_ml_domain = self._extract_ai_ml_domain(desc_lower, title_lower)
        
        # Stage 4: Tech stack matching
        tech_stack = self._match_tech_stack(desc_lower)
        
        # Stage 5: Location and visa
        location_visa = self._extract_location_visa(desc_lower, location)
        
        # Stage 6: Company signals
        company_signals = self._extract_company_signals(desc_lower)
        
        # Determine overall suitability
        is_suitable = (
            not dealbreakers['has_dealbreakers'] and
            (graduate_signals['accepts_fresh_grads'] or 
             graduate_signals['years_required'] is not None and graduate_signals['years_required'] <= 2)
        )
        
        # Calculate parsing confidence
        confidence = self._calculate_confidence({
            'dealbreakers': dealbreakers,
            'graduate_signals': graduate_signals,
            'ai_ml_domain': ai_ml_domain,
            'tech_stack': tech_stack,
            'location_visa': location_visa
        })
        
        return {
            'is_graduate_suitable': is_suitable,
            'dealbreakers': dealbreakers,
            'graduate_signals': graduate_signals,
            'ai_ml_domain': ai_ml_domain,
            'tech_stack_match': tech_stack,
            'location_visa': location_visa,
            'company_signals': company_signals,
            'parsing_metadata': {
                'confidence': confidence,
                'method': 'regex',
                'description_length': len(job_description),
                'has_description': len(job_description.strip()) > 100
            }
        }
    
    def _check_dealbreakers(self, desc: str, title: str) -> Dict:
        """Check for automatic rejection criteria"""
        reasons = []
        
        # PR/Citizenship requirement
        if self.patterns['pr_citizenship'].search(desc):
            reasons.append("Requires Australian PR/Citizenship/Security Clearance")
        
        # Senior level in title or description
        if self.patterns['senior_level'].search(title) or \
           (self.patterns['senior_level'].search(desc) and 
            not re.search(r'\b(junior|graduate|entry)', desc, re.IGNORECASE)):
            reasons.append("Senior/Lead level position")
        
        # 3+ years experience required
        years_match = self.patterns['years_excessive'].search(desc)
        if years_match:
            reasons.append(f"Requires {years_match.group(1)}+ years of experience")
        
        # PhD required
        if self.patterns['phd_required'].search(desc):
            reasons.append("PhD required")
        
        return {
            'has_dealbreakers': len(reasons) > 0,
            'reasons': reasons
        }
    
    def _extract_graduate_signals(self, desc: str, title: str) -> Dict:
        """Extract signals indicating graduate-friendliness"""
        
        # Check for explicit graduate role
        is_explicit_grad = bool(self.patterns['explicit_graduate'].search(desc) or 
                                self.patterns['explicit_graduate'].search(title))
        
        # Check for entry-level indicators
        is_entry_level = bool(self.patterns['entry_level'].search(desc) or 
                             self.patterns['entry_level'].search(title))
        
        # Extract years of experience required
        years_required = None
        years_match = self.patterns['years_0_2'].search(desc)
        if years_match:
            years_str = years_match.group(1)
            if '-' in years_str:
                years_required = int(years_str.split('-')[1])  # Take upper bound
            else:
                years_required = int(years_str)
        
        # Check for Masters degree mention
        masters_mentioned = bool(self.patterns['masters_preferred'].search(desc))
        
        # Determine seniority level
        if is_explicit_grad:
            seniority = 'Graduate'
        elif is_entry_level:
            seniority = 'Junior/Entry-level'
        elif years_required is not None and years_required <= 1:
            seniority = 'Entry-level'
        else:
            seniority = 'Unknown'
        
        # Extract relevant keywords
        keywords = []
        if is_explicit_grad:
            match = self.patterns['explicit_graduate'].search(desc)
            if match:
                keywords.append(match.group(0))
        if is_entry_level:
            match = self.patterns['entry_level'].search(desc)
            if match:
                keywords.append(match.group(0))
        if years_match:
            keywords.append(years_match.group(0))
        
        return {
            'is_explicit_graduate_role': is_explicit_grad,
            'seniority_level': seniority,
            'years_required': years_required,
            'accepts_fresh_grads': is_explicit_grad or is_entry_level or (years_required is not None and years_required <= 1),
            'masters_mentioned': masters_mentioned,
            'keywords': keywords[:5]  # Limit to top 5
        }
    
    def _extract_ai_ml_domain(self, desc: str, title: str) -> Dict:
        """Identify AI/ML domain and role type"""
        
        domains = {
            'Machine Learning': bool(self.patterns['machine_learning'].search(desc)),
            'Deep Learning': bool(self.patterns['deep_learning'].search(desc)),
            'Computer Vision': bool(self.patterns['computer_vision'].search(desc)),
            'Agentic AI': bool(self.patterns['agentic_ai'].search(desc)),
            'LLM/RAG': bool(self.patterns['llm_rag'].search(desc)),
            'MLOps': bool(self.patterns['mlops'].search(desc)),
            'Data Science': bool(self.patterns['data_science'].search(desc))
        }
        
        # Find primary domain (first True)
        primary_domain = None
        for domain, present in domains.items():
            if present:
                primary_domain = domain
                break
        
        # Check if it's an AI/ML role
        is_ai_ml = any(domains.values())
        
        # Extract domain keywords
        domain_keywords = []
        for pattern_name in ['agentic_ai', 'llm_rag', 'computer_vision', 
                             'machine_learning', 'deep_learning', 'mlops']:
            matches = self.patterns[pattern_name].finditer(desc)
            for match in matches:
                keyword = match.group(0).lower()
                if keyword not in domain_keywords:
                    domain_keywords.append(keyword)
                if len(domain_keywords) >= 10:
                    break
        
        return {
            'primary_domain': primary_domain or 'Unknown',
            'is_ai_ml_role': is_ai_ml,
            'domains_present': [d for d, present in domains.items() if present],
            'domain_keywords': domain_keywords[:10],
            'role_type': 'Technical IC'  # Assume IC for graduate roles
        }
    
    def _match_tech_stack(self, desc: str) -> Dict:
        """Match required tech stack against profile skills (dynamically loaded from keywords)"""
        
        # Extract all mentioned skills from description
        mentioned_skills = set()
        for skill in self.PROFILE_SKILLS:
            # Use word boundaries for accurate matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, desc, re.IGNORECASE):
                mentioned_skills.add(skill)
        
        # Categorize skills
        your_skills_present = mentioned_skills & self.PROFILE_SKILLS
        
        # Distinguish required vs preferred (simple heuristic)
        required_context = r'(required|must have|essential|mandatory|necessary)'
        preferred_context = r'(preferred|nice to have|bonus|desirable|plus)'
        
        required_skills = set()
        preferred_skills = set()
        
        for skill in mentioned_skills:
            # Check context around skill mention
            pattern = r'(.{0,50}\b' + re.escape(skill) + r'\b.{0,50})'
            matches = re.finditer(pattern, desc, re.IGNORECASE)
            
            is_required = False
            is_preferred = False
            
            for match in matches:
                context = match.group(1).lower()
                if re.search(required_context, context):
                    is_required = True
                if re.search(preferred_context, context):
                    is_preferred = True
            
            # Default to required if no clear signal
            if is_required or (not is_preferred and not is_required):
                required_skills.add(skill)
            else:
                preferred_skills.add(skill)
        
        # Calculate match percentage
        matched_required = required_skills & self.PROFILE_SKILLS
        missing_required = required_skills - self.PROFILE_SKILLS
        
        match_percentage = 100
        if required_skills:
            match_percentage = int((len(matched_required) / len(required_skills)) * 100)
        
        return {
            'required_skills': sorted(list(required_skills))[:15],
            'preferred_skills': sorted(list(preferred_skills))[:10],
            'matched_required': sorted(list(matched_required))[:15],
            'missing_required': sorted(list(missing_required))[:10],
            'match_percentage': match_percentage,
            'your_strong_skills_present': sorted(list(your_skills_present & self.STRONG_KEYWORDS))
        }
    
    def _extract_location_visa(self, desc: str, location_str: str) -> Dict:
        """Extract location and visa information (uses dynamic location preferences)"""
        
        # Find cities mentioned (from user's location preferences in jobs.txt)
        cities_found = {}
        combined_text = (desc + ' ' + location_str.lower()).lower()
        
        for city, score in self.LOCATION_SCORES.items():
            if re.search(r'\b' + city + r'\b', combined_text):
                cities_found[city.title()] = score
        
        # Determine remote type
        remote_type = 'Unknown'
        remote_days = None
        
        if self.patterns['remote_full'].search(desc):
            remote_type = 'Fully Remote'
        elif self.patterns['hybrid'].search(desc):
            remote_type = 'Hybrid'
            # Try to extract days
            hybrid_match = re.search(r'(\d+)\s*days?\s*(in[\s-]office|onsite|office)', desc, re.IGNORECASE)
            if hybrid_match:
                remote_days = int(hybrid_match.group(1))
        elif re.search(r'\b(onsite|office[\s-]based|in[\s-]office)\b', desc, re.IGNORECASE):
            remote_type = 'Onsite'
        
        # Calculate preference score
        preference_score = 0
        if cities_found:
            preference_score = max(cities_found.values())
        elif remote_type == 'Fully Remote' and 'australia' in combined_text:
            preference_score = 80  # Australia remote
        elif remote_type == 'Fully Remote':
            preference_score = 60  # International remote
        
        # Visa requirements
        requires_pr = bool(self.patterns['pr_citizenship'].search(desc))
        sponsorship_offered = bool(self.patterns['visa_sponsorship'].search(desc))
        
        return {
            'cities_mentioned': list(cities_found.keys()),
            'primary_city': max(cities_found, key=cities_found.get) if cities_found else None,
            'remote_type': remote_type,
            'remote_days_office': remote_days,
            'preference_score': preference_score,
            'requires_pr': requires_pr,
            'sponsorship_offered': sponsorship_offered,
            'visa_acceptable': not requires_pr or sponsorship_offered,
            'is_location_blocker': requires_pr and not sponsorship_offered
        }
    
    def _extract_company_signals(self, desc: str) -> Dict:
        """Extract company culture and growth signals"""
        
        mentions_mentorship = bool(self.patterns['mentorship'].search(desc))
        mentions_growth = bool(self.patterns['growth'].search(desc))
        
        # Try to extract team size
        team_size = None
        team_match = re.search(r'(\d+)[\s-]?(person|member|engineer)s?\s+(team|ml|ai|data)', desc, re.IGNORECASE)
        if team_match:
            team_size = f"{team_match.group(1)}-person {team_match.group(3)} team"
        
        # Detect company stage
        company_stage = 'Unknown'
        if re.search(r'\b(startup|early[\s-]stage|series\s+[a-c]|seed\s+funded)\b', desc, re.IGNORECASE):
            company_stage = 'Startup'
        elif re.search(r'\b(scale[\s-]up|series\s+[d-f]|growth\s+stage)\b', desc, re.IGNORECASE):
            company_stage = 'Scale-up'
        elif re.search(r'\b(enterprise|fortune\s+500|multinational|global\s+leader|established)\b', desc, re.IGNORECASE):
            company_stage = 'Enterprise'
        
        return {
            'mentions_mentorship': mentions_mentorship,
            'mentions_growth': mentions_growth,
            'mentions_learning': mentions_mentorship or mentions_growth,
            'team_size': team_size,
            'company_stage': company_stage
        }
    
    def _calculate_confidence(self, parsed_data: Dict) -> float:
        """Calculate parsing confidence score (0-1)"""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on what we found
        if parsed_data['dealbreakers']['has_dealbreakers']:
            confidence += 0.2  # High confidence in rejection
        
        if parsed_data['graduate_signals']['years_required'] is not None:
            confidence += 0.15
        
        if parsed_data['graduate_signals']['is_explicit_graduate_role']:
            confidence += 0.2
        
        if parsed_data['ai_ml_domain']['is_ai_ml_role']:
            confidence += 0.1
        
        if parsed_data['tech_stack']['required_skills']:
            confidence += 0.15
        
        if parsed_data['location_visa']['primary_city']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _empty_result(self, reason: str) -> Dict:
        """Return empty parsing result"""
        return {
            'is_graduate_suitable': False,
            'dealbreakers': {'has_dealbreakers': True, 'reasons': [reason]},
            'graduate_signals': {},
            'ai_ml_domain': {},
            'tech_stack_match': {},
            'location_visa': {},
            'company_signals': {},
            'parsing_metadata': {'confidence': 0.0, 'method': 'none', 'error': reason}
        }
    
    def format_for_display(self, parsed_data: Dict) -> str:
        """Format parsed data for human-readable display"""
        
        lines = []
        lines.append("=" * 70)
        lines.append("PARSED JOB ANALYSIS")
        lines.append("=" * 70)
        
        # Graduate suitability
        if parsed_data['is_graduate_suitable']:
            lines.append("✓ GRADUATE SUITABLE: Yes")
        else:
            lines.append("✗ GRADUATE SUITABLE: No")
            if parsed_data['dealbreakers']['has_dealbreakers']:
                lines.append("\nDEALBREAKERS:")
                for reason in parsed_data['dealbreakers']['reasons']:
                    lines.append(f"  ✗ {reason}")
        
        # Graduate signals
        gs = parsed_data.get('graduate_signals', {})
        if gs:
            lines.append(f"\nSENIORITY: {gs.get('seniority_level', 'Unknown')}")
            if gs.get('years_required') is not None:
                lines.append(f"EXPERIENCE: {gs['years_required']} years")
            if gs.get('is_explicit_graduate_role'):
                lines.append("✓ Explicit Graduate Program")
        
        # AI/ML domain
        domain = parsed_data.get('ai_ml_domain', {})
        if domain.get('is_ai_ml_role'):
            lines.append(f"\nDOMAIN: {domain.get('primary_domain', 'AI/ML')}")
            if domain.get('domain_keywords'):
                lines.append(f"Keywords: {', '.join(domain['domain_keywords'][:5])}")
        
        # Tech stack
        tech = parsed_data.get('tech_stack_match', {})
        if tech.get('match_percentage') is not None:
            lines.append(f"\nTECH MATCH: {tech['match_percentage']}%")
            if tech.get('your_strong_skills_present'):
                lines.append(f"Your strengths: {', '.join(tech['your_strong_skills_present'][:5])}")
            if tech.get('missing_required'):
                lines.append(f"Missing: {', '.join(tech['missing_required'][:5])}")
        
        # Location
        loc = parsed_data.get('location_visa', {})
        if loc.get('primary_city'):
            lines.append(f"\nLOCATION: {loc['primary_city']} ({loc.get('remote_type', 'Unknown')})")
            lines.append(f"Preference Score: {loc.get('preference_score', 0)}/100")
        
        lines.append("=" * 70)
        return '\n'.join(lines)


# Convenience function for quick parsing
def parse_job(description: str, title: str = "", location: str = "") -> Dict:
    """
    Quick parse function
    
    Usage:
        parsed = parse_job(job['description'], job['title'], job['location'])
    """
    parser = JobDescriptionParser()
    return parser.parse(description, title, location)


if __name__ == "__main__":
    # Test the parser
    test_description = """
    We are seeking a Junior Machine Learning Engineer to join our growing AI team in Melbourne.
    
    Requirements:
    - Masters degree in Computer Science, AI, or related field
    - 0-1 years of professional experience
    - Strong Python and PyTorch skills
    - Experience with computer vision and object detection
    - Knowledge of Docker and MLOps practices
    
    Preferred:
    - Experience with LangChain or similar frameworks
    - Azure ML experience
    - FastAPI development
    
    We offer mentorship, learning opportunities, and a clear career progression path.
    This role is hybrid with 3 days in office.
    """
    
    parser = JobDescriptionParser()
    result = parser.parse(test_description, "Junior ML Engineer", "Melbourne, Australia")
    
    print(parser.format_for_display(result))
    print("\nFull JSON:")
    print(json.dumps(result, indent=2))
