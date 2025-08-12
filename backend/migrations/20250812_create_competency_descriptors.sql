-- Migration: Create competency_descriptors table for dynamic archetype generation
CREATE TABLE IF NOT EXISTS competency_descriptors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    competency_key VARCHAR(64) NOT NULL,
    tier ENUM('Low', 'Medium', 'High') NOT NULL,
    descriptor_phrase TEXT NOT NULL,
    UNIQUE KEY (competency_key, tier)
);

-- Example inserts (expand as needed)
INSERT INTO competency_descriptors (competency_key, tier, descriptor_phrase) VALUES
('decision_making', 'Low', 'requiring foundational decision-making based on clear guidelines.'),
('decision_making', 'Medium', 'requiring proactive and independent decision-making in complex situations.'),
('decision_making', 'High', 'mastery of Decision Making as a critical supporting competency.'),
('strategic_planning', 'Low', 'requiring a basic awareness of long-term goals to inform daily tasks.'),
('strategic_planning', 'Medium', 'requiring the ability to develop and execute strategic plans.'),
('strategic_planning', 'High', 'mastery of Strategic Planning for organizational impact.'),
('problem_solving', 'Low', 'requiring the ability to troubleshoot routine problems using established solutions.'),
('problem_solving', 'Medium', 'requiring creative and analytical problem-solving.'),
('problem_solving', 'High', 'mastery of Problem Solving to drive innovation.'),
('prioritization', 'Low', 'requiring the ability to follow a prioritized list of tasks effectively.'),
('prioritization', 'Medium', 'requiring the ability to prioritize tasks independently in dynamic environments.'),
('prioritization', 'High', 'mastery of Prioritization as a signature skill.'),
('communication', 'Low', 'requiring clear and concise communication on technical or operational matters.'),
('communication', 'Medium', 'requiring the ability to communicate complex ideas clearly to diverse audiences.'),
('communication', 'High', 'mastery of Communication as a critical supporting competency.'),
('collaboration', 'Low', 'requiring the ability to be a productive and reliable team member.'),
('collaboration', 'Medium', 'requiring the ability to lead and collaborate across teams.'),
('collaboration', 'High', 'mastery of Collaboration for cross-functional success.'),
('stakeholder_management', 'Low', 'requiring the ability to respond to stakeholder requests and manage expectations on defined tasks.'),
('stakeholder_management', 'Medium', 'requiring the ability to manage stakeholder relationships proactively.'),
('stakeholder_management', 'High', 'skillfully navigate competing demands from diverse stakeholders.'),
('negotiation', 'Low', 'requiring basic negotiation skills for straightforward, well-defined issues.'),
('negotiation', 'Medium', 'requiring the ability to negotiate favorable outcomes in complex scenarios.'),
('negotiation', 'High', 'mastery of Negotiation as a strategic asset.'),
('domain_tools', 'Low', 'requiring a foundational knowledge of the core platforms and tools used in the role.'),
('domain_tools', 'Medium', 'requiring the ability to leverage domain tools for professional productivity.'),
('domain_tools', 'High', 'mastery of Domain Tools for strategic advantage.'),
('data_analysis', 'Low', 'requiring the ability to read and understand pre-built reports and dashboards.'),
('data_analysis', 'Medium', 'professional standard of competence in Data Analysis.'),
('data_analysis', 'High', 'mastery of Data Analysis for data-driven decision making.'),
('documentation', 'Low', 'requiring the ability to produce clear and understandable documentation for personal or team use.'),
('documentation', 'Medium', 'requiring the ability to document complex processes and knowledge.'),
('documentation', 'High', 'mastery of Documentation for organizational learning.');
