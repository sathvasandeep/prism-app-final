"""
Phrase Library for Dynamic Archetype Generation

This module defines the database schema and data for competency descriptor phrases
used to generate dynamic archetype narratives based on proficiency tiers.

Proficiency Tiers:
- Low (1-3): Foundational Requirement
- Medium (4-7): Professional Competence Required  
- High (8-10): Strategic Mastery Required
"""

# Database schema for competency_descriptors table
CREATE_COMPETENCY_DESCRIPTORS_TABLE = """
CREATE TABLE IF NOT EXISTS competency_descriptors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    skive_category ENUM('skills', 'knowledge', 'identity', 'values', 'ethics') NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    proficiency_tier ENUM('low', 'medium', 'high') NOT NULL,
    descriptor_phrase TEXT NOT NULL,
    narrative_type ENUM('signature', 'supporting', 'foundational') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_descriptor (skive_category, subcategory, proficiency_tier, narrative_type)
);
"""

# Seed data for the phrase library
COMPETENCY_DESCRIPTORS_SEED_DATA = [
    # SKILLS - Cognitive
    ('skills', 'Decision Making', 'low', 'requiring foundational decision-making based on clear guidelines', 'foundational'),
    ('skills', 'Decision Making', 'medium', 'requiring independent decision-making with moderate complexity and stakeholder impact', 'supporting'),
    ('skills', 'Decision Making', 'high', 'requiring masterful decision-making under uncertainty with significant organizational impact', 'signature'),
    
    ('skills', 'Strategic Planning', 'low', 'requiring basic awareness of long-term goals to inform daily tasks', 'foundational'),
    ('skills', 'Strategic Planning', 'medium', 'requiring active participation in strategic planning with departmental scope', 'supporting'),
    ('skills', 'Strategic Planning', 'high', 'requiring visionary strategic planning that shapes organizational direction', 'signature'),
    
    ('skills', 'Problem Solving', 'low', 'requiring ability to troubleshoot routine problems using established solutions', 'foundational'),
    ('skills', 'Problem Solving', 'medium', 'requiring creative problem-solving for complex, multi-faceted challenges', 'supporting'),
    ('skills', 'Problem Solving', 'high', 'requiring innovative problem-solving that creates new frameworks and approaches', 'signature'),
    
    ('skills', 'Prioritization', 'low', 'requiring ability to follow a prioritized list of tasks effectively', 'foundational'),
    ('skills', 'Prioritization', 'medium', 'requiring skillful prioritization across competing demands and limited resources', 'supporting'),
    ('skills', 'Prioritization', 'high', 'requiring ruthless prioritization that drives organizational focus and resource allocation', 'signature'),
    
    # SKILLS - Interpersonal
    ('skills', 'Communication', 'low', 'requiring clear and concise communication on technical or operational matters', 'foundational'),
    ('skills', 'Communication', 'medium', 'requiring persuasive communication across diverse audiences and contexts', 'supporting'),
    ('skills', 'Communication', 'high', 'requiring masterful storytelling and communication that inspires and drives change', 'signature'),
    
    ('skills', 'Collaboration', 'low', 'requiring ability to be a productive and reliable team member', 'foundational'),
    ('skills', 'Collaboration', 'medium', 'requiring leadership in cross-functional collaboration and team dynamics', 'supporting'),
    ('skills', 'Collaboration', 'high', 'requiring orchestration of complex collaborative ecosystems across organizations', 'signature'),
    
    ('skills', 'Stakeholder Management', 'low', 'requiring ability to respond to stakeholder requests and manage expectations on defined tasks', 'foundational'),
    ('skills', 'Stakeholder Management', 'medium', 'requiring proactive stakeholder relationship building and conflict resolution', 'supporting'),
    ('skills', 'Stakeholder Management', 'high', 'requiring diplomatic mastery in managing competing stakeholder interests and building consensus', 'signature'),
    
    ('skills', 'Negotiation', 'low', 'requiring basic negotiation skills for straightforward, well-defined issues', 'foundational'),
    ('skills', 'Negotiation', 'medium', 'requiring strategic negotiation across complex, multi-party scenarios', 'supporting'),
    ('skills', 'Negotiation', 'high', 'requiring masterful negotiation that creates win-win outcomes in high-stakes situations', 'signature'),
    
    # SKILLS - Technical
    ('skills', 'Domain Tools', 'low', 'requiring foundational knowledge of core platforms and tools used in the role', 'foundational'),
    ('skills', 'Domain Tools', 'medium', 'requiring advanced proficiency in domain-specific tools and platforms', 'supporting'),
    ('skills', 'Domain Tools', 'high', 'requiring expert-level mastery and innovation in domain tools and technology', 'signature'),
    
    ('skills', 'Data Analysis', 'low', 'requiring ability to read and understand pre-built reports and dashboards', 'foundational'),
    ('skills', 'Data Analysis', 'medium', 'requiring independent data analysis and insight generation for decision support', 'supporting'),
    ('skills', 'Data Analysis', 'high', 'requiring advanced analytics leadership that drives data-driven organizational strategy', 'signature'),
    
    ('skills', 'Documentation', 'low', 'requiring ability to produce clear and understandable documentation for personal or team use', 'foundational'),
    ('skills', 'Documentation', 'medium', 'requiring comprehensive documentation that enables knowledge transfer and process improvement', 'supporting'),
    ('skills', 'Documentation', 'high', 'requiring strategic documentation that creates organizational knowledge assets and standards', 'signature'),
    
    # KNOWLEDGE - Domain Expertise
    ('knowledge', 'Industry Knowledge', 'low', 'requiring basic understanding of industry trends and competitive landscape', 'foundational'),
    ('knowledge', 'Industry Knowledge', 'medium', 'requiring deep industry expertise that informs strategic recommendations', 'supporting'),
    ('knowledge', 'Industry Knowledge', 'high', 'requiring thought leadership and industry expertise that shapes market direction', 'signature'),
    
    ('knowledge', 'Regulatory Compliance', 'low', 'requiring awareness of relevant regulations and compliance requirements', 'foundational'),
    ('knowledge', 'Regulatory Compliance', 'medium', 'requiring active management of compliance processes and risk mitigation', 'supporting'),
    ('knowledge', 'Regulatory Compliance', 'high', 'requiring strategic compliance leadership that anticipates and shapes regulatory changes', 'signature'),
    
    ('knowledge', 'Market Dynamics', 'low', 'requiring basic understanding of market forces and customer needs', 'foundational'),
    ('knowledge', 'Market Dynamics', 'medium', 'requiring sophisticated market analysis that drives product and strategy decisions', 'supporting'),
    ('knowledge', 'Market Dynamics', 'high', 'requiring visionary market insight that identifies and creates new opportunities', 'signature'),
    
    # IDENTITY - Professional Identity
    ('identity', 'Role Clarity', 'low', 'requiring clear understanding of role boundaries and responsibilities', 'foundational'),
    ('identity', 'Role Clarity', 'medium', 'requiring confident role ownership with ability to expand scope appropriately', 'supporting'),
    ('identity', 'Role Clarity', 'high', 'requiring role definition and evolution that shapes organizational structure', 'signature'),
    
    ('identity', 'Professional Growth', 'low', 'requiring commitment to continuous learning and skill development', 'foundational'),
    ('identity', 'Professional Growth', 'medium', 'requiring proactive career development and mentorship of others', 'supporting'),
    ('identity', 'Professional Growth', 'high', 'requiring thought leadership and industry influence that advances the profession', 'signature'),
    
    # VALUES - Organizational Alignment
    ('values', 'Integrity', 'low', 'requiring consistent ethical behavior and transparency in all interactions', 'foundational'),
    ('values', 'Integrity', 'medium', 'requiring moral leadership that builds trust and sets ethical standards', 'supporting'),
    ('values', 'Integrity', 'high', 'requiring unwavering integrity that defines organizational culture and values', 'signature'),
    
    ('values', 'Customer Focus', 'low', 'requiring awareness of customer needs and impact of decisions on customer experience', 'foundational'),
    ('values', 'Customer Focus', 'medium', 'requiring customer-centric decision making that drives satisfaction and loyalty', 'supporting'),
    ('values', 'Customer Focus', 'high', 'requiring visionary customer advocacy that transforms organizational culture', 'signature'),
    
    # ETHICS - Moral Reasoning
    ('ethics', 'Ethical Decision Making', 'low', 'requiring recognition of ethical implications and consultation when needed', 'foundational'),
    ('ethics', 'Ethical Decision Making', 'medium', 'requiring independent ethical reasoning in complex, ambiguous situations', 'supporting'),
    ('ethics', 'Ethical Decision Making', 'high', 'requiring ethical leadership that establishes moral frameworks for the organization', 'signature'),
    
    ('ethics', 'Social Responsibility', 'low', 'requiring awareness of social impact and commitment to responsible practices', 'foundational'),
    ('ethics', 'Social Responsibility', 'medium', 'requiring active promotion of social responsibility and sustainable practices', 'supporting'),
    ('ethics', 'Social Responsibility', 'high', 'requiring visionary leadership in corporate social responsibility and societal impact', 'signature'),
]

def get_proficiency_tier(score: float) -> str:
    """Convert 1-10 scale to proficiency tier"""
    if score <= 3:
        return 'low'
    elif score <= 7:
        return 'medium'
    else:
        return 'high'

def get_narrative_type(tier: str, is_signature: bool = False) -> str:
    """Determine narrative type based on tier and signature status"""
    if is_signature:
        return 'signature'
    elif tier == 'high':
        return 'supporting'
    else:
        return 'foundational'
