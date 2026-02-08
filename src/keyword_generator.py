"""
Keyword Generator - AI-Powered Role-Agnostic Keyword Extraction

This module automatically generates relevant keywords, skills, and filters
from a jobs.txt file using AI (DeepSeek). Makes the entire workflow
adapt to ANY job role without manual configuration.

Usage:
    python -m src.keyword_generator

Future-Ready:
    - Designed for multi-tenant SaaS (per-user keyword generation)
    - Caches results to avoid redundant API calls
    - Detects jobs.txt changes via hash comparison
"""

import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import requests


class KeywordGenerator:
    """Generate role-specific keywords from job titles using AI"""
    
    def __init__(self, jobs_file: str = "jobs.txt", output_file: str = "generated_keywords.json"):
        self.jobs_file = jobs_file
        self.output_file = output_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from config.json"""
        with open("config.json", "r") as f:
            return json.load(f)
    
    def _get_jobs_txt_content(self) -> Dict[str, Any]:
        """Parse jobs.txt file and extract all sections"""
        if not os.path.exists(self.jobs_file):
            raise FileNotFoundError(f"{self.jobs_file} not found!")
        
        with open(self.jobs_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Also read profile.txt if it exists for skills extraction
        profile_content = ""
        profile_path = Path("profile.txt")
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_content = f.read()
        
        result = {
            "job_titles": "",
            "dealbreakers": {},
            "preferences": {},
            "optimization": {},
            "raw_content": content,
            "profile_content": profile_content
        }
        
        # Extract job titles (everything before [DEALBREAKERS] or end of file)
        lines = content.split("\n")
        job_titles_lines = []
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith("#"):
                continue
            
            # Detect section headers
            if line_stripped.startswith("[") and line_stripped.endswith("]"):
                current_section = line_stripped[1:-1].lower()
                continue
            
            # Parse based on current section
            if current_section is None:
                # Before any section = job titles
                job_titles_lines.append(line_stripped)
            elif current_section == "dealbreakers":
                if ":" in line_stripped:
                    key, value = line_stripped.split(":", 1)
                    result["dealbreakers"][key.strip()] = value.strip()
            elif current_section == "preferences":
                if ":" in line_stripped:
                    key, value = line_stripped.split(":", 1)
                    result["preferences"][key.strip()] = value.strip()
            elif current_section == "optimization":
                if ":" in line_stripped:
                    key, value = line_stripped.split(":", 1)
                    result["optimization"][key.strip()] = value.strip()
        
        result["job_titles"] = " ".join(job_titles_lines)
        return result
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of jobs.txt content"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def needs_regeneration(self) -> bool:
        """Check if keywords need to be regenerated based on jobs.txt changes"""
        if not os.path.exists(self.output_file):
            return True
        
        jobs_content = self._get_jobs_txt_content()
        current_hash = self._calculate_hash(jobs_content["raw_content"])
        
        with open(self.output_file, "r") as f:
            existing = json.load(f)
        
        return existing.get("jobs_txt_hash") != current_hash
    
    def generate_keywords(self, force: bool = False) -> Dict[str, Any]:
        """
        Generate keywords from jobs.txt using DeepSeek AI
        
        Args:
            force: Force regeneration even if hash matches
            
        Returns:
            Dictionary containing all generated keywords
        """
        # Check if regeneration needed
        if not force and not self.needs_regeneration():
            print("✅ Keywords are up-to-date (jobs.txt unchanged)")
            with open(self.output_file, "r") as f:
                return json.load(f)
        
        print("🔄 Generating keywords from jobs.txt...")
        
        # Parse jobs.txt
        jobs_data = self._get_jobs_txt_content()
        job_titles = jobs_data["job_titles"]
        
        if not job_titles:
            raise ValueError("No job titles found in jobs.txt!")
        
        # Prepare AI prompt
        prompt = self._create_prompt(jobs_data)
        
        # Call DeepSeek API
        keywords = self._call_ai_api(prompt)
        
        # Add metadata
        keywords.update({
            "jobs_txt_hash": self._calculate_hash(jobs_data["raw_content"]),
            "generated_at": datetime.now().isoformat(),
            "job_titles_count": len(job_titles.split(",")),
            "source_file": self.jobs_file,
            "dealbreakers": jobs_data["dealbreakers"],
            "preferences": jobs_data["preferences"],
            "optimization": jobs_data["optimization"]
        })
        
        # Save to file
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(keywords, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Keywords generated and saved to {self.output_file}")
        print(f"   - Title required keywords: {len(keywords.get('title_required_keywords', []))}")
        print(f"   - Title required phrases: {len(keywords.get('title_required_phrases', []))}")
        print(f"   - Title exclude keywords: {len(keywords.get('title_exclude_keywords', []))}")
        print(f"   - Acronym mappings: {len(keywords.get('acronym_mappings', {}))}")
        print(f"   - False positive patterns: {len(keywords.get('false_positive_patterns', []))}")
        print(f"   - Description keywords: {len(keywords.get('description_required_keywords', []))}")
        print(f"   - Description quality threshold: {keywords.get('description_quality_threshold', 2)}")
        
        return keywords
    
    def _create_prompt(self, jobs_data: Dict) -> str:
        """Create AI prompt for keyword generation with 13 universal patterns"""
        job_titles = jobs_data["job_titles"]
        dealbreakers = jobs_data.get("dealbreakers", {})
        profile_content = jobs_data.get("profile_content", "")
        
        # Extract key info from profile if available
        profile_summary = ""
        if profile_content:
            profile_summary = f"""
USER PROFILE/SKILLS (extract relevant keywords from this):
{profile_content[:2000]}...
"""
        
        prompt = f"""You are an expert job search keyword analyzer. Analyze the target job titles, dealbreakers, and user profile to generate comprehensive, UNIVERSAL keywords that work for ANY job type (AI, Marketing, Finance, Backend, Sales, etc.).

TARGET JOB TITLES:
{job_titles}

DEALBREAKERS:
{json.dumps(dealbreakers, indent=2) if dealbreakers else "None provided"}
{profile_summary}

Your task: Generate keywords following 13 UNIVERSAL PATTERNS that apply to any job domain:

PATTERN 1: Core Field-Specific Roles
- Identify the core domain (AI/ML/Marketing/Finance/Backend/etc.) from job titles
- Generate keywords SPECIFIC to that domain
- DO NOT include generic role words alone (engineer, developer, analyst, software)
- ONLY include domain-specific combinations (ai engineer, ml developer, data analyst)

PATTERN 2: Desired Seniority Level
- Extract seniority from job titles (Graduate/Junior/Associate/Entry-Level)
- Generate variations (junior, graduate, entry level, associate, early career)

PATTERN 3: Excluded Seniority (from dealbreakers)
- Use exclude_seniority from dealbreakers to filter senior roles
- Generate patterns to catch Senior/Lead/Principal/Manager variants

PATTERN 4: Generic Roles WITHOUT User's Field
- Generic "Developer" alone → MUST REJECT (not in title_required_keywords)
- Generic "Engineer" alone → MUST REJECT
- Generic "Analyst" alone → MUST REJECT
- Generic "Software" alone → MUST REJECT
- These words should ONLY appear in title_exclude_keywords or NOT AT ALL

PATTERN 5: Generic Roles WITH User's Field Integration
- "Full Stack AI Engineer" → ACCEPT only because "ai" keyword present
- "Marketing Data Analyst" → ACCEPT only if "data" keyword present
- DO NOT include "full stack", "software engineer", "developer" as standalone keywords
- ONLY include domain-specific phrases like "ai engineer", "ml developer"

PATTERN 6: Adjacent Field Roles
- For AI: Data Engineering, Analytics acceptable
- For Marketing: Growth, Content Strategy acceptable
- Identify 2-3 adjacent fields from job titles and profile

PATTERN 7: Hybrid/Cross-Functional Roles
- "AI Product Manager" might be acceptable if AI-focused
- Generate patterns for domain + function hybrids

PATTERN 8: Desired Program Types
- Graduate programs, internships, apprenticeships
- Extract from job titles (Graduate/Intern/Trainee)

PATTERN 9: Borderline Technologies/Skills
- For AI: Data Engineering, Analytics (adjacent, might be OK)
- For Backend: DevOps, Infrastructure (adjacent)
- Identify borderline skills from profile

PATTERN 10: Non-Core Function Roles (FALSE POSITIVES)
- "AI Sales Engineer" → REJECT (Sales primary, AI secondary)
- "Marketing AI Specialist" → REJECT (Marketing primary)
- Generate false positive patterns: domain + non-core function

PATTERN 11: Multi-Word Phrase Matching
- "Machine Learning" is different from "Machine" + "Learning"
- Generate 50 multi-word phrases that MUST match exactly
- Examples: "machine learning", "data science", "computer vision"

PATTERN 12: Acronym Expansion
- ML ↔ Machine Learning
- AI ↔ Artificial Intelligence
- Generate bidirectional mappings for common acronyms

PATTERN 13: False Positive Prevention
- "AI Marketing Manager" → domain + excluded function
- Generate 20 regex patterns to catch false positives early
- Examples: "(?i)(ai|ml|data)\\s+(sales|marketing|hr|recruiting)"

Generate JSON with these keys:

{{
  "title_required_keywords": [150 words],  // PATTERN 1: Core domain keywords (ai, machine learning, backend, react, etc.)
  "title_required_phrases": [50 phrases],  // PATTERN 11: Multi-word phrases ("machine learning", "data science")
  "title_exclude_keywords": [25 words],    // PATTERN 10: Non-core functions (sales, marketing, hr, recruiting)
  "acronym_mappings": {{...}},              // PATTERN 12: {{"ml": "machine learning", "ai": "artificial intelligence"}}
  "false_positive_patterns": [20 patterns], // PATTERN 13: Regex patterns like "(?i)(ai|ml)\\s+(sales|marketing)"
  "description_required_keywords": [200 words], // Technical terms for description quality check
  "description_quality_threshold": 2,       // Minimum keyword matches required in description
  "description_min_length": 100,            // Minimum description length
  "technical_skills": [60 items],           // LEGACY: Keep for compatibility
  "strong_keywords": [25 items],            // LEGACY: Keep for compatibility  
  "exclude_keywords": [30 items],           // PATTERN 4: Generic non-technical jobs (retail, warehouse, etc.)
  "adjacent_roles": [20 items],             // PATTERN 6: Adjacent field roles
  "search_keywords": [30 items]             // LEGACY: Keep for compatibility
}}

CRITICAL INSTRUCTIONS:
- Extract domain from job titles (AI/ML, Marketing, Finance, Backend, etc.)
- title_required_keywords: 150 unique DOMAIN-SPECIFIC words (lowercase, no duplicates)
  * NEVER include generic role words alone: engineer, developer, analyst, software, programmer
  * ONLY domain-specific: ai, machine, learning, nlp, vision, data, scientist, mlops, etc.
  * If domain is AI/ML: include ai, ml, machine, learning, deep, neural, vision, nlp, data, scientist, mlops, etc.
  * Generic role words should be in title_exclude_keywords instead
- title_required_phrases: 50 multi-word DOMAIN-SPECIFIC exact-match phrases
  * Examples: "machine learning", "data science", "ai engineer", "computer vision"
  * NOT: "software engineer", "developer", "full stack developer"
- title_exclude_keywords: 25 non-core function words (sales, marketing, hr, recruiting, AND generic role words WITHOUT domain context)
- acronym_mappings: 10-15 common acronyms in this domain
- false_positive_patterns: 20 regex patterns (format: "(?i)pattern")
- description_required_keywords: 200 unique technical terms (lowercase)
- All arrays must have unique values (no duplicates)
- Ensure proper JSON format (no trailing commas, escape special chars)

Return ONLY valid JSON. No markdown, no explanations, no duplicates.
"""
        return prompt
    
    def _call_ai_api(self, prompt: str) -> Dict[str, Any]:
        """Call DeepSeek API to generate keywords"""
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = self.config.get("openrouter_api_key", "")
        
        if not api_key:
            raise ValueError("OpenRouter API key not found in config.json!")
        
        # Load keyword generation config
        keygen_config = self.config.get('keyword_generation', {})
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/job-scraper",
            "X-Title": "Job Scraper Keyword Generator"
        }
        
        payload = {
            "model": self.config.get("ai_models", {}).get("primary", "deepseek/deepseek-chat"),
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert keyword analyzer for job search optimization. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": keygen_config.get('temperature', 0.3),  # Load from config
            "max_tokens": keygen_config.get('max_tokens', 8000)  # Load from config
        }
        
        print("   Calling DeepSeek API...")
        response = requests.post(api_url, headers=headers, json=payload, timeout=keygen_config.get('timeout', 120))
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            keywords = json.loads(content.strip())
            return keywords
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {e}\n\nResponse:\n{content}")
    
    def get_cached_keywords(self) -> Dict[str, Any]:
        """Load cached keywords from file"""
        if not os.path.exists(self.output_file):
            raise FileNotFoundError(f"{self.output_file} not found! Run generate_keywords() first.")
        
        with open(self.output_file, "r") as f:
            return json.load(f)


def main():
    """CLI entry point"""
    import sys
    
    force = "--force" in sys.argv
    
    generator = KeywordGenerator()
    
    if force:
        print("🔄 Force regeneration mode...")
    
    try:
        keywords = generator.generate_keywords(force=force)
        
        print("\n📊 GENERATED KEYWORDS SUMMARY:")
        print(f"   Technical Skills: {len(keywords.get('technical_skills', []))}")
        print(f"   Title Keywords: {len(keywords.get('title_keywords', []))}")
        print(f"   Description Keywords: {len(keywords.get('description_keywords', []))}")
        print(f"   Strong Keywords: {len(keywords.get('strong_keywords', []))}")
        print(f"   Exclude Keywords: {len(keywords.get('exclude_keywords', []))}")
        print(f"   Search Keywords: {len(keywords.get('search_keywords', []))}")
        print(f"\n✅ Keywords saved to: {generator.output_file}")
        
        # Show sample
        print("\n📋 SAMPLE KEYWORDS:")
        print(f"   Technical Skills: {', '.join(keywords.get('technical_skills', [])[:10])}...")
        print(f"   Strong Keywords: {', '.join(keywords.get('strong_keywords', [])[:5])}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
