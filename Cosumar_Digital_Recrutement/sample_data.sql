BEGIN;

-- Drop auth-related sequences
DROP SEQUENCE IF EXISTS auth_group_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_group_permissions_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_permission_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_user_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_user_groups_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_user_user_permissions_id_seq CASCADE;

-- Drop auth-related tables
DROP TABLE IF EXISTS auth_user_user_permissions CASCADE;
DROP TABLE IF EXISTS auth_user_groups CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;
DROP TABLE IF EXISTS auth_group_permissions CASCADE;
DROP TABLE IF EXISTS auth_group CASCADE;
DROP TABLE IF EXISTS auth_permission CASCADE;

-- Drop session table
DROP TABLE IF EXISTS django_session CASCADE;

COMMIT;

INSERT INTO resume_service_domaine (nom, keywords) VALUES
('Informatique', '[
  "Java", "Python", "C", "C++", "C#", "Go", "Rust", "Ruby", "Kotlin", "Scala",
  "Spring Boot", "Django", "Flask", "FastAPI", "Express.js", "NestJS", "ASP.NET", "Laravel", "Symfony",
  "React", "Vue.js", "Angular", "Svelte", "Next.js", "Nuxt.js", "jQuery",
  "HTML5", "CSS3", "SASS", "LESS", "Tailwind", "Bootstrap", "Material UI",
  "MySQL", "PostgreSQL", "MongoDB", "Cassandra", "Redis", "SQLite", "Oracle", "MS SQL Server", "InfluxDB",
  "REST API", "GraphQL", "SOAP", "gRPC", "WebSocket",
  "Git", "GitHub", "GitLab", "Bitbucket", "CI/CD", "Jenkins", "CircleCI", "Travis CI", "GitHub Actions",
  "Docker", "Kubernetes", "Ansible", "Terraform", "Helm", "Vagrant",
  "Linux", "Ubuntu", "CentOS", "Shell", "Bash", "PowerShell", "Zsh",
  "AWS", "Azure", "Google Cloud", "Firebase", "DigitalOcean", "Heroku", "Netlify",
  "Agile", "Scrum", "Kanban", "XP", "TDD", "BDD", "DDD",
  "Jira", "Confluence", "Notion", "Trello", "Asana", "Slack", "Zoom"
]'),
('Génie Civil', '[
  "AutoCAD", "Revit", "Civil 3D", "ArchiCAD", "SketchUp", "Tekla Structures",
  "ETABS", "SAP2000", "STAAD.Pro", "Plaxis", "Robot Structural Analysis", "CSI Bridge",
  "BIM", "BTP", "VRD", "Topographie", "GPS Trimble", "Nivellement", "SIG", "QGIS",
  "Béton armé", "Charpente métallique", "Routes", "Ponts", "Ouvrages d''art", "Canalisations",
  "Normes Eurocodes", "DTU", "NF EN", "Sécurité chantier", "Planning Gantt", "MS Project", "Primavera P6"
]'),
('Finance', '[
  "Comptabilité", "IFRS", "IAS", "Audit", "Contrôle de gestion", "Planification budgétaire",
  "Analyse financière", "Bilan", "Compte de résultat", "Cash flow", "Valorisation", "Modélisation financière",
  "ERP SAP FI/CO", "Oracle Finance", "SAGE", "Odoo", "Power BI", "Tableau", "Qlik", "Excel VBA",
  "Banque", "Crédit", "Gestion de portefeuille", "Titres", "Marchés financiers", "Dérivés", "Forex", "Trading",
  "KYC", "AML", "Conformité", "Gestion des risques", "Réglementation bancaire", "Bâle III", "Solvency II"
]'),
('Gestion', '[
  "Gestion de projet", "PMI", "Prince2", "PMP", "Lean", "Six Sigma", "Kaizen", "5S", "DMAIC",
  "Scrum", "Kanban", "SAFe", "Agilité à l''échelle",
  "OKR", "KPI", "Balanced Scorecard", "Dashboard", "Budget", "Reporting",
  "ERP", "SAP", "Oracle", "Odoo", "CRM", "Salesforce", "Zoho", "HubSpot",
  "Change management", "Leadership", "Coaching", "Résolution de problèmes", "Communication"
]'),
('Design', '[
  "UX Design", "UI Design", "Design thinking", "Wireframe", "Prototype", "Responsive design", "Accessibilité",
  "Figma", "Adobe XD", "Sketch", "InVision", "Zeplin", "Framer", "Marvel", "Balsamiq",
  "Photoshop", "Illustrator", "InDesign", "Lightroom", "Canva", "CorelDraw",
  "After Effects", "Premiere Pro", "Cinema 4D", "Blender", "Unity", "Unreal Engine",
  "Branding", "Identité visuelle", "Motion design", "Typographie", "Palette de couleurs", "Grille UI"
]'),
('Santé', '[
  "GMP", "BPF", "GxP", "ISO 13485", "ISO 15189", "FDA CFR 21", "ICH Guidelines",
  "Pharmacovigilance", "Essais cliniques", "R&D", "Biotechnologie", "Chimie organique", "Chimie analytique",
  "HPLC", "GC-MS", "Spectroscopie", "PCR", "ELISA", "Immunologie", "Microbiologie", "Hématologie",
  "LIMS", "Bioanalyse", "Formulation", "Stabilité", "Validation de méthode", "Contrôle qualité"
]'),
('Logistique', '[
  "Supply Chain", "Gestion des stocks", "Planification", "MRP", "DRP", "Prévision de la demande",
  "WMS", "TMS", "ERP SAP MM", "Odoo", "Oracle SCM", "SAGE X3", "Microsoft Dynamics",
  "Achats", "Procurement", "Sourcing", "Appels d''offres", "Contrats fournisseurs",
  "Incoterms", "Transport international", "Import/export", "3PL", "Douanes", "Logistique inverse"
]'),
('Énergie', '[
  "Énergies renouvelables", "Photovoltaïque", "Éolien", "Hydraulique", "Biomasse", "Cogénération",
  "Smart Grid", "Microgrid", "Réseau intelligent", "Bilan carbone", "Audit énergétique",
  "ISO 14001", "ISO 50001", "HQE", "BREEAM", "LEED", "RSE", "Analyse du cycle de vie", "Éco-conception",
  "Génie climatique", "Efficacité énergétique", "Transition énergétique"
]'),
('Droit', '[
  "Droit des affaires", "Droit du travail", "Droit pénal", "Droit civil", "Droit fiscal",
  "RGPD", "KYC", "AML", "LBA", "Conformité réglementaire", "ISSC", "Droit bancaire", "Droit international",
  "Contrats", "Litiges", "Procédures judiciaires", "Arbitrage", "Médiation", "Jurisprudence", "Code civil"
]'),
('Ressources Humaines', '[
  "Recrutement", "Sourcing", "Entretien", "Onboarding", "Formation", "Développement des compétences",
  "Gestion des talents", "Plan de succession", "Évaluation de la performance", "Rémunération",
  "Droit du travail", "Relations sociales", "Climat social", "Gestion des conflits",
  "SIRH", "PeopleSoft", "SAP SuccessFactors", "Workday", "Oracle HCM Cloud"
]'),
('Vente', '[
  "Prospection", "Négociation", "Closing", "CRM", "Salesforce", "HubSpot", "Zoho CRM",
  "Lead generation", "Account management", "Key account management", "B2B", "B2C",
  "Stratégie commerciale", "Plan d''action commercial", "Objectifs de vente", "Reporting commercial",
  "Techniques de vente", "Pitching", "Cross-selling", "Up-selling"
]'),
('Industrie', '[
  "Automatisation", "Robotique", "CNC", "FAO", "CAO", "Lean manufacturing", "Kaizen",
  "Maintenance préventive", "Maintenance prédictive", "TPM", "5S", "SMED",
  "ISO 9001", "ISO 14001", "ISO 45001", "IATF 16949", "AS9100",
  "Processus industriels", "Chaîne de production", "Contrôle qualité", "Amélioration continue"
]'),
('Marketing', '[
  "Marketing digital", "SEO", "SEA", "SMO", "SMM", "Content marketing", "Inbound marketing", "Outbound marketing",
  "Growth hacking", "Email marketing", "Automation", "Lead generation", "CRM", "Branding",
  "Google Analytics", "Google Ads", "Facebook Ads", "LinkedIn Ads", "Hotjar", "HubSpot", "Mailchimp",
  "Storytelling", "Copywriting", "Social media", "Community management", "Funnel", "Persona", "AB Testing"
]');
