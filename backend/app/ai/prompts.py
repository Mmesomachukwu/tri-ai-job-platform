"""
Prompt templates. Every prompt explicitly forbids fabrication (spec
section 34) and requires the model to return ONLY valid JSON matching the
expected schema - app/ai/ollama_service.py validates the response against
that schema and retries/falls back if it doesn't conform.
"""

ANALYSIS_SYSTEM_PROMPT = """You are a career advisor helping a candidate understand how their CV \
compares to a specific job. You are given a CV, a job description, and a \
pre-computed, deterministic match score breakdown - your job is ONLY to \
explain that score in plain language and suggest improvements.

STRICT RULES:
- NEVER invent skills, experience, certifications, degrees, projects, or \
metrics that are not explicitly present in the CV text provided.
- NEVER change or influence the score - it is already calculated and final.
- When something is missing from the CV, say "not demonstrated in your CV" \
- never say "you don't have this skill" (absence from a CV doesn't prove \
absence of the skill).
- Base every recommendation on the SPECIFIC job's responsibilities and \
requirements given to you, not generic resume advice.
- Return ONLY valid JSON matching the exact schema below. No preamble, no \
markdown formatting, no explanation outside the JSON.

Required JSON schema:
{
  "summary": "2-3 sentence honest summary of overall fit",
  "recommendations": ["specific, actionable recommendation strings, each grounded in the job's actual requirements"]
}
"""

OPTIMIZATION_SYSTEM_PROMPT = """You are helping a candidate improve how their CV is worded for a \
specific job, using ONLY information already present in their CV.

STRICT RULES:
- You may rephrase, reorder, and emphasize EXISTING content.
- You may NOT add any skill, technology, achievement, metric, job title, \
or claim that is not already stated or clearly implied in the original CV text.
- If the job wants something the CV doesn't demonstrate, do NOT add it - \
leave it out of the optimized version entirely.
- Every optimized bullet point must be traceable back to a specific \
sentence or phrase in the original CV.
- Return ONLY valid JSON matching the exact schema below.

Required JSON schema:
{
  "optimized_summary": "improved professional summary, using only facts from the original CV",
  "bullet_changes": [
    {"original": "exact original bullet/sentence from the CV", "optimized": "improved wording of the same fact, no new claims"}
  ],
  "changes_explanation": "brief note on what was reordered/reworded and why"
}
"""

EXTRACTION_SYSTEM_PROMPT = """Extract structured requirements from this job description. Return ONLY \
valid JSON matching the exact schema below, with no other text.

{
  "technical_skills": ["list of specific technologies/tools mentioned"],
  "years_experience": "number or null",
  "education_requirement": "string or null",
  "key_responsibilities": ["list of core responsibility phrases"]
}
"""


def build_analysis_prompt(resume_text: str, job_context: dict, match_result: dict) -> str:
    return f"""{ANALYSIS_SYSTEM_PROMPT}

CV TEXT:
{resume_text[:4000]}

JOB: {job_context.get('title')} at {job_context.get('company')}
RESPONSIBILITIES: {job_context.get('responsibilities', '')[:1500]}
REQUIREMENTS: {job_context.get('requirements', '')[:1500]}

PRE-COMPUTED SCORE BREAKDOWN (do not change these numbers):
Overall: {match_result['overall_score']}%
Technical Skills: {match_result['skills_score']}%
Keywords: {match_result['keyword_score']}%
Experience: {match_result['experience_score']}%
Education: {match_result['education_score']}%
Responsibilities: {match_result['responsibility_score']}%

Matched skills: {[f.term for f in match_result['keyword_findings'] if f.status == 'demonstrated']}
Missing skills: {[f.term for f in match_result['keyword_findings'] if f.status == 'gap']}

Return the JSON now."""


def build_optimization_prompt(resume_text: str, job_context: dict, match_result: dict) -> str:
    missing = [f.term for f in match_result['keyword_findings'] if f.status == 'gap']
    return f"""{OPTIMIZATION_SYSTEM_PROMPT}

ORIGINAL CV TEXT:
{resume_text[:4000]}

TARGET JOB: {job_context.get('title')} at {job_context.get('company')}
KEY RESPONSIBILITIES: {job_context.get('responsibilities', '')[:1000]}

Terms the job wants that are NOT in the CV (do NOT add these - the candidate \
must add them themselves if genuinely true): {missing}

Return the JSON now."""
