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
        
        result = {
            "job_titles": "",
            "dealbreakers": {},
            "preferences": {},
            "optimization": {},
            "raw_content": content
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
        print(f"   - Technical skills: {len(keywords.get('technical_skills', []))}")
        print(f"   - Title keywords: {len(keywords.get('title_keywords', []))}")
        print(f"   - Description keywords: {len(keywords.get('description_keywords', []))}")
        
        return keywords
    
    def _create_prompt(self, jobs_data: Dict) -> str:
        """Create AI prompt for keyword generation"""
        job_titles = jobs_data["job_titles"]
        dealbreakers = jobs_data.get("dealbreakers", {})
        
        prompt = f"""You are an expert job search keyword analyzer. Analyze these target job titles and generate comprehensive keywords for job scraping and filtering.

TARGET JOB TITLES:
{job_titles}

DEALBREAKERS (if provided):
{json.dumps(dealbreakers, indent=2) if dealbreakers else "None provided - use general search"}

Generate the following in JSON format:

1. **technical_skills** (40-60 items): Relevant technical skills, tools, frameworks, languages for these roles.
   - Include programming languages, frameworks, libraries, tools
   - Include both common and specialized technologies
   - Examples for AI roles: Python, TensorFlow, PyTorch, LangChain, OpenAI, AWS
   - Examples for Finance roles: Excel, SQL, Bloomberg, Financial Modeling, VBA
   - Examples for Marketing roles: Google Analytics, SEO, SEM, HubSpot, Adobe Creative

2. **title_keywords** (30-50 items): Keywords that should appear in relevant job titles.
   - Include role names, seniority levels, specializations
   - Include synonyms and variations
   - Examples for AI: ai, machine learning, ml, data scientist, mlops, computer vision
   - Examples for Finance: analyst, accountant, financial, investment, portfolio
   - Examples for Marketing: marketing, digital, content, social media, brand

3. **description_keywords** (50-80 items): Technical terms that should appear in job descriptions.
   - Include methodologies, concepts, processes, domains
   - Include industry-specific jargon
   - Examples for AI: model, algorithm, neural network, deep learning, nlp, training
   - Examples for Finance: valuation, forecasting, budgeting, p&l, roi, financial statements
   - Examples for Marketing: campaign, engagement, conversion, analytics, brand awareness

4. **strong_keywords** (15-25 items): Must-have keywords that strongly indicate relevance.
   - These are non-negotiable terms for the role
   - Examples for AI: machine learning, deep learning, neural network, computer vision, nlp
   - Examples for Finance: financial analysis, investment, portfolio management
   - Examples for Marketing: marketing strategy, digital marketing, campaign management

5. **exclude_keywords** (20-30 items): Keywords that indicate COMPLETELY NON-TECHNICAL jobs.
   - CRITICAL: Exclude ONLY jobs with ZERO technical/analytical component
   - DO NOT exclude industry names (finance, business, consulting) - target roles can exist in ANY industry
   - Examples to EXCLUDE: sales representative, retail cashier, warehouse worker, truck driver, construction laborer
   - Examples to EXCLUDE: nursing, teaching (non-technical), receptionist, customer service rep
   - Examples to KEEP: "AI in Finance" is valid, "Business Analyst" can be valid, "Consulting" can involve tech
   - Focus on: Pure manual labor, pure sales (no tech), pure hospitality, pure admin roles
   - If a keyword could apply to a technical role in that industry, DO NOT exclude it

6. **adjacent_roles** (10-20 items): Related roles that might be relevant.
   - Roles that use similar skills but different titles
   - Examples for AI: algorithm engineer, research engineer, quantitative analyst
   - Examples for Finance: business analyst, data analyst, risk analyst
   - Examples for Marketing: growth hacker, content strategist, community manager

7. **search_keywords** (20-30 items): Optimized keywords for job board searches.
   - Best keywords to use when constructing search URLs
   - Should be broad enough to capture all relevant jobs
   - Examples for AI: ai engineer, ml engineer, data scientist, computer vision
   - Examples for Finance: financial analyst, junior accountant, investment analyst

IMPORTANT:
- Focus on keywords SPECIFIC to these job titles
- Include both formal and informal terminology
- Consider industry-specific variations
- Include emerging technologies/trends in the field
- Be comprehensive to avoid missing relevant jobs
- All keywords should be lowercase for matching

Return ONLY valid JSON with these exact keys. No explanations.
"""
        return prompt
    
    def _call_ai_api(self, prompt: str) -> Dict[str, Any]:
        """Call DeepSeek API to generate keywords"""
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = self.config.get("openrouter_api_key", "")
        
        if not api_key:
            raise ValueError("OpenRouter API key not found in config.json!")
        
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
            "temperature": 0.3,  # Lower temperature for consistent output
            "max_tokens": 4000
        }
        
        print("   Calling DeepSeek API...")
        response = requests.post(api_url, headers=headers, json=payload)
        
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
