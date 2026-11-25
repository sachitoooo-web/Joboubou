import json
import re
from openai import OpenAI


def analyze_opportunity(
    openai_api_key: str,
    cv_profiles: dict,
    news_title: str,
    news_snippet: str,
    news_source: str,
    company_hint: str = "",
    model: str = "gpt-6-luna",
) -> dict:
    """Analyse une actualité suisse via OpenAI, score le potentiel de recrutement et choisit le bon CV."""
    client = OpenAI(api_key=openai_api_key)

    cvs_context = "\n".join(
        [
            f"- {cv_id} ({info['lang']}): {info['summary']} | Idéal pour: {info['best_for']}"
            for cv_id, info in cv_profiles.items()
        ]
    )

    system_prompt = (
        "Tu es un chasseur de têtes stratégique spécialisé sur le marché suisse "
        "(Suisse romande, Genève, Berne, Zurich). Tu réponds exclusivement en JSON valide, "
        "sans texte avant ni après."
    )

    user_prompt = f"""
Analyse cette actualité récente pour détecter si une organisation suisse va probablement avoir besoin
de recruter dans les 1 à 6 prochains mois sur un profil Affaires Publiques / Stratégie / Partenariats / R&I / Normalisation,
choisis l'unique meilleur CV parmi les 5 variantes ci-dessous, et rédige une approche spontanée chirurgicale (zéro blabla).

=== LES 5 CV DE LA CANDIDATE (Meriem Naimi, basée à Lausanne, citoyenne UE) ===
{cvs_context}

=== ACTUALITÉ DÉTECTÉE ===
Entreprise pressentie (si connue) : {company_hint or "À identifier depuis l'article"}
Titre : {news_title}
Extrait : {news_snippet}
Source : {news_source}

=== CONSIGNES STRICTES ===
1. Identifie le nom EXACT de l'entreprise ou organisation suisse concernée (si article générique sans organisation claire, mets hiring_score à 0).
2. Attribue un `hiring_score` réaliste et sévère de 0 à 100 :
   - 80-100 : Signal fort direct (levée de fonds, gain projet Horizon Europe/Innosuisse, nouvelle BU, coalition/partenariat majeur, nouvelle stratégie Suisse-UE) + forte adéquation avec un des 5 CV.
   - 50-79 : Signal intéressant mais besoin indirect ou structure plus petite.
   - 0-49 : Hors-sujet, article trop généraliste, ou faible lien avec le profil.
3. Sélectionne l'unique `recommended_cv` parmi les clés exactes : {list(cv_profiles.keys())}.
4. Choisis la `language` de candidature ("FR" ou "EN") adaptée à l'organisation et au CV choisi.
5. Rédige :
   - `draft_email_subject` : Objet court et percutant faisant référence à l'actualité.
   - `draft_email_body` : Email de candidature spontanée de 130-170 mots max :
     (1) Accroche précise sur l'actualité détectée,
     (2) Proposition de valeur concrète chiffrée issue du CV choisi (ex: 3,5 M€ Horizon Europe, IEC Genève 170 experts, portefeuille Énergie, etc.),
     (3) Appel à l'action sobre (échange de 15 min, basée à Lausanne / Suisse).
   - `draft_linkedin_msg` : Note d'invitation LinkedIn (< 290 caractères).

Retourne UNIQUEMENT un objet JSON respectant exactement cette structure :
{{
  "company_name": "string",
  "canton_or_city": "string (ex: Vaud / Lausanne, Genève, Zurich, Berne, Suisse)",
  "hiring_score": 0,
  "recommended_cv": "string",
  "language": "FR ou EN",
  "target_role": "Intitulé de poste probable à proposer",
  "rationale": "Explication concise en 2 phrases du pourquoi cette boîte va recruter et pourquoi ce CV matche.",
  "draft_email_subject": "string",
  "draft_email_body": "string",
  "draft_linkedin_msg": "string"
}}
"""

    # Note : on ne passe volontairement pas `temperature` pour rester 100% compatible
    # avec les modèles à raisonnement natif (GPT-6 / GPT-5).
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw_text = response.choices[0].message.content or "{}"
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())
    return json.loads(cleaned)