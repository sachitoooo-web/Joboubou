CV_PROFILES = {
    "CV_CLEANTECH_FR": {
        "filename": "Meriem NAIMI_CV_SWISSCLEANTECH.pdf",
        "lang": "FR",
        "summary": (
            "Développement stratégique, Affaires publiques et internationales, Partenariats "
            "(Énergie, Environnement, Politique industrielle, Transformation numérique). "
            "6+ ans d'exp : AFNOR (pilotage portefeuille Énergie 600 k€, montage Horizon Europe/EISMEA 3,5 M€+, "
            "CEN-CENELEC/ISO/IEC), Secrétaire IEC Genève (170+ experts), Paris-Saclay, KAM Acolad (1 M€+ ENGIE, EDF, ABB). "
            "Basée à Lausanne, citoyenne UE, FR/EN C2, AR/ES C1, DE A2."
        ),
        "best_for": "Énergéticiens suisses, cleantechs francophones, partenariats industriels, décarbonation en Suisse romande."
    },
    "CV_PORTFOLIO_EN": {
        "filename": "CV_Meriem_Naimi_IEC.pdf",
        "lang": "EN",
        "summary": (
            "Portfolio Strategy, Business Development, International Standardization "
            "(Energy Transition, Industrial Transformation, R&I, Digital Innovation). "
            "AFNOR Energy BU (€500K revenue, service offerings, market intelligence), IEC TC 1 Assistant Secretary (Geneva), "
            "Acolad Key Account Manager (€2-4M accounts, €1M+ new contracts with ENGIE, EDF, ABB, Sumitomo). "
            "Domains: Digital Product Passports, Critical Raw Materials, AI, Quantum, Cybersecurity."
        ),
        "best_for": "Multinationales industrielles/tech en Suisse (EN), postes Business Development, Portfolio Strategy, Standardization."
    },
    "CV_GOVERNANCE_EN": {
        "filename": "CV - Meriem NAIMI - Industry_International_Affairs_EN.pdf",
        "lang": "EN",
        "summary": (
            "Strategic Partnerships, Governance, International Programmes "
            "(Environment, Innovation, Energy Transition). "
            "Multistakeholder engagement across governments, industry, academia & IOs; €3.5M+ collaborative funding, "
            "represented CEN-CENELEC at European Commission High-Level Forum, convened 170+ experts at IEC Geneva, "
            "high-level conferences (ISO General Meeting 2026)."
        ),
        "best_for": "Organisations internationales (Genève), ONG climat/énergie, fondations, forums multilatéraux, gouvernance tech."
    },
    "CV_RI_EN": {
        "filename": "Meriem NAIMI - CV_R&I.pdf",
        "lang": "EN",
        "summary": (
            "Research & Innovation Funding Strategy, International Programmes, Collaborative R&D. "
            "Horizon Europe & EISMEA consortium building and grant management (€3.5M+: Stand4Quant, ACCELERATE, EPre-QT, DPP-Connect), "
            "Université Paris-Saclay international research partnerships & mobility (Fulbright, MOPGA, CSC), "
            "deep tech domains (AI, Quantum, Cybersecurity, DPP, Circular Economy)."
        ),
        "best_for": "Universités/EPFL/ETH, centres de R&D (CSEM, PSI, Empa), startups DeepTech/Quantum/Cleantech cherchant des fonds EU/Innosuisse."
    },
    "CV_AFFPUB_FR": {
        "filename": "Meriem_Naimi_CV_Responsables de projets.pdf",
        "lang": "FR",
        "summary": (
            "Affaires publiques, Communication stratégique, Relations institutionnelles "
            "(Énergie, Environnement, Politique industrielle, Transformation numérique). "
            "Représentation d'intérêts économiques, notes de positionnement, veille réglementaire, "
            "dialogue public-privé, relations Suisse-UE et compétitivité en Suisse romande."
        ),
        "best_for": "Fédérations professionnelles, associations faîtières suisses, cabinets d'affaires publiques et lobbying en Suisse romande/Berne."
    }
}

SWISS_RADAR_PRESETS = {
    "Cleantech & Énergie (Suisse romande)": {
        "lang": "fr",
        "queries": [
            '("levée de fonds" OR "nouveau partenariat" OR "expansion" OR "décarbonation") ("énergie" OR "cleantech" OR "solaire") (Suisse OR Vaud OR Lausanne OR Genève)',
            '("nouveau projet" OR "investissement" OR "stratégie énergétique") ("Romande Energie" OR "Alpiq" OR "Groupe E" OR "BKW" OR "cleantech") Suisse',
        ],
        "decision_makers": '("Head of Public Affairs" OR "Directeur Stratégie" OR "Responsable Partenariats" OR "CEO" OR "Head of Sustainability" OR "DRH")'
    },
    "DeepTech, R&I & Financements EU/Innosuisse": {
        "lang": "en",
        "queries": [
            '("Horizon Europe" OR "Innosuisse" OR "Series A" OR "Series B" OR "consortium") (Switzerland OR Lausanne OR Geneva OR Zurich) ("quantum" OR "AI" OR "cleantech" OR "energy" OR "circular")',
            '("research partnership" OR "EU funding" OR "innovation hub") (EPFL OR CSEM OR ETH OR Switzerland) ("energy" OR "digital" OR "sustainability")',
        ],
        "decision_makers": '("VP R&D" OR "Head of Innovation" OR "Grants Manager" OR "Head of Partnerships" OR "Chief Strategy Officer" OR "CTO")'
    },
    "Organisations Internationales & Gouvernance (Genève)": {
        "lang": "en",
        "queries": [
            '("new initiative" OR "coalition" OR "strategic partnership" OR "funding") (Geneva OR Switzerland) ("energy transition" OR "climate" OR "AI governance" OR "standards")',
            '("launches" OR "announces" OR "grant") ("Geneva" OR "Gland") ("sustainability" OR "decarbonization" OR "technology governance")',
        ],
        "decision_makers": '("Head of Partnerships" OR "Programme Director" OR "Director of Policy" OR "Head of Governance" OR "Talent Acquisition")'
    },
    "Affaires Publiques & Fédérations (Suisse-UE)": {
        "lang": "fr",
        "queries": [
            '("relations Suisse-UE" OR "politique énergétique" OR "politique industrielle" OR "réglementation") ("fédération" OR "association" OR "economiesuisse" OR "swisscleantech" OR "Swissmem") Suisse',
            '("affaires publiques" OR "nouvelle stratégie" OR "nomination") (Lausanne OR Genève OR Berne) ("énergie" OR "industrie" OR "numérique")',
        ],
        "decision_makers": '("Directeur" OR "Secrétaire général" OR "Responsable affaires publiques" OR "Head of Public Affairs" OR "Partner")'
    },
    "Industrie, ESG & Normalisation (Suisse EN)": {
        "lang": "en",
        "queries": [
            '("Digital Product Passport" OR "CSRD" OR "CBAM" OR "decarbonization" OR "critical raw materials") (Switzerland OR Zurich OR Basel OR Geneva) ("company" OR "industrial" OR "expansion")',
            '("new business unit" OR "strategic partnership" OR "acquisition") ("ABB" OR "Sulzer" OR "Hitachi Energy" OR "SGS" OR "Climeworks" OR "South Pole" OR "Quantis") Switzerland',
        ],
        "decision_makers": '("VP Strategy" OR "Head of Business Development" OR "Head of Regulatory" OR "Head of Sustainability" OR "VP Public Affairs")'
    }
}