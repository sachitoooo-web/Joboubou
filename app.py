import hmac
import pandas as pd
import streamlit as st
from pypdf import PdfReader
from supabase import create_client

from analyzer import analyze_opportunity
from config import CV_PROFILES, SWISS_RADAR_PRESETS
from scanner import find_company_domain, find_decision_makers, serper_search

st.set_page_config(
    page_title="Swiss Hiring Radar — Multi-CV",
    page_icon="🇨🇭",
    layout="wide",
)


# --- Helpers ---
def get_secret(key: str, default: str = "") -> str:
    try:
        val = st.secrets.get(key, default)
        return str(val).strip() if val is not None else default
    except Exception:
        return default


def require_password():
    """Bloque l'accès à l'application tant que le mot de passe n'est pas validé."""
    expected_pwd = get_secret("APP_PASSWORD")
    if not expected_pwd:
        st.error(
            "Aucun `APP_PASSWORD` configuré dans les Secrets Streamlit. "
            "Ajoute `APP_PASSWORD = \"...\"` dans Manage app > Settings > Secrets."
        )
        st.stop()

    if st.session_state.get("authenticated", False):
        return

    _, col_center, _ = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("## 🇨🇭 Swiss Hiring Radar")
        st.caption("Accès privé — veuillez saisir le mot de passe.")
        with st.form("login_form"):
            pwd_input = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
            if submitted:
                if hmac.compare_digest(pwd_input, expected_pwd):
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect.")
    st.stop()


def get_supabase(url: str, key: str):
    if url and key:
        clean_url = url.rstrip("/")
        if clean_url.endswith("/rest/v1"):
            clean_url = clean_url[:-8]
        try:
            return create_client(clean_url, key)
        except Exception as e:
            st.sidebar.error(f"Erreur Supabase : {e}")
    return None


def save_opportunity(sb, record: dict):
    if "local_opps" not in st.session_state:
        st.session_state.local_opps = []
    existing_urls = {x.get("signal_url") for x in st.session_state.local_opps}
    if record.get("signal_url") not in existing_urls:
        st.session_state.local_opps.insert(0, record)

    if sb:
        try:
            sb.table("opportunities").upsert(record, on_conflict="signal_url").execute()
        except Exception as e:
            st.warning(f"Sauvegarde Supabase ignorée ({e})")


def load_opportunities(sb) -> list:
    if sb:
        try:
            res = (
                sb.table("opportunities")
                .select("*")
                .order("hiring_score", desc=True)
                .limit(200)
                .execute()
            )
            return res.data or []
        except Exception as e:
            st.warning(f"Lecture Supabase impossible ({e}), affichage session locale.")
    return st.session_state.get("local_opps", [])


# --- 1. Vérification du mot de passe avant tout chargement ---
require_password()


# --- 2. Chargement des clés côté serveur uniquement (invisibles dans l'UI) ---
openai_key = get_secret("OPENAI_API_KEY")
serper_key = get_secret("SERPER_API_KEY")
sb_url = get_secret("SUPABASE_URL")
sb_key = get_secret("SUPABASE_KEY")
sb = get_supabase(sb_url, sb_key)


# --- 3. Initialisation des 5 CV en session ---
if "cv_profiles" not in st.session_state:
    st.session_state.cv_profiles = {k: dict(v) for k, v in CV_PROFILES.items()}


# --- 4. Sidebar épurée (aucune clé affichée) ---
with st.sidebar:
    st.title("🇨🇭 Swiss Hiring Radar")
    st.caption("Anticipation de recrutements • Multi-CV")

    model_choice = st.selectbox(
        "Modèle OpenAI",
        ["gpt-6-luna", "gpt-5.4-mini", "gpt-6.2-sol"],
        index=0,
        help="gpt-6-luna : rapide et économique pour les scans en masse. gpt-6.2-sol : qualité maximale.",
    )

    min_score = st.slider(
        "Score minimum pour chercher les contacts LinkedIn",
        30,
        90,
        60,
        5,
    )

    st.divider()

    if openai_key and serper_key:
        st.success("Moteur IA & Radar actifs")
    else:
        st.error("Clés API manquantes dans les Secrets Streamlit.")

    if sb:
        st.success("Base de données connectée")
    else:
        st.info("Mode local (export CSV dispo)")

    st.divider()
    if st.button("🔒 Se déconnecter", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()


# --- 5. Onglets principaux ---
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📡 Radar Automatique Suisse",
        "🎯 Scanner une liste d'entreprises",
        "📋 Pipeline & Candidatures",
        "📄 Gestion des 5 CV",
    ]
)


# ==========================================
# ONGLET 1 : RADAR AUTOMATIQUE PAR SECTEUR
# ==========================================
with tab1:
    st.subheader("Détection de signaux faibles en Suisse")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        segment = st.selectbox("Écosystème cible", list(SWISS_RADAR_PRESETS.keys()))
    with col2:
        period_map = {
            "7 derniers jours": "qdr:w",
            "30 derniers jours": "qdr:m",
            "3 derniers mois": "qdr:y",
        }
        period_label = st.selectbox(
            "Fraîcheur des actualités", list(period_map.keys()), index=1
        )
    with col3:
        max_articles = st.number_input("Max articles / scan", min_value=3, max_value=20, value=8)

    custom_query = st.text_input(
        "Ou requête Google News personnalisée (laisser vide pour le preset)"
    )

    if st.button("🚀 Lancer le Radar", type="primary", use_container_width=True):
        if not openai_key or not serper_key:
            st.error("Vérifie `OPENAI_API_KEY` et `SERPER_API_KEY` dans les Secrets Streamlit.")
        else:
            preset = SWISS_RADAR_PRESETS[segment]
            queries = [custom_query] if custom_query.strip() else preset["queries"]
            raw_news = []

            with st.status("Scan des actualités suisses en cours...", expanded=True) as status:
                for q in queries:
                    st.write(f"🔎 Requête : `{q}`")
                    items = serper_search(
                        serper_key,
                        q,
                        search_type="news",
                        lang=preset["lang"],
                        time_range=period_map[period_label],
                        num=max_articles,
                    )
                    raw_news.extend(items)

                unique_news = list(
                    {n.get("link"): n for n in raw_news if n.get("link")}.values()
                )[:max_articles]
                st.write(
                    f"📰 {len(unique_news)} actualités uniques trouvées. Analyse via `{model_choice}`..."
                )

                found_count = 0
                for item in unique_news:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    source = item.get("source", "")
                    link = item.get("link", "")
                    date_str = item.get("date", "")

                    try:
                        analysis = analyze_opportunity(
                            openai_key,
                            st.session_state.cv_profiles,
                            title,
                            snippet,
                            source,
                            model=model_choice,
                        )
                    except Exception as e:
                        st.write(f"⚠️ Erreur OpenAI sur '{title[:40]}...' : {e}")
                        continue

                    score = int(analysis.get("hiring_score", 0))
                    company = analysis.get("company_name", "Inconnue")

                    if score < 30 or not company or company.lower() == "inconnue":
                        continue

                    contacts = []
                    domain = ""
                    if score >= min_score:
                        st.write(
                            f"✅ **{company}** (Score {score}/100 → `{analysis['recommended_cv']}`). "
                            f"Recherche des décideurs..."
                        )
                        domain = find_company_domain(serper_key, company)
                        contacts = find_decision_makers(
                            serper_key, company, preset["decision_makers"], domain
                        )

                    record = {
                        "company_name": company,
                        "domain": domain,
                        "canton_or_city": analysis.get("canton_or_city", "Suisse"),
                        "segment": segment,
                        "signal_title": title,
                        "signal_url": link,
                        "signal_date": date_str,
                        "hiring_score": score,
                        "recommended_cv": analysis.get("recommended_cv", ""),
                        "language": analysis.get("language", "FR"),
                        "target_role": analysis.get("target_role", ""),
                        "rationale": analysis.get("rationale", ""),
                        "contacts": contacts,
                        "draft_email_subject": analysis.get("draft_email_subject", ""),
                        "draft_email_body": analysis.get("draft_email_body", ""),
                        "draft_linkedin_msg": analysis.get("draft_linkedin_msg", ""),
                        "status": "À contacter" if score >= min_score else "Veille",
                    }
                    save_opportunity(sb, record)
                    found_count += 1

                status.update(
                    label=f"Scan terminé : {found_count} opportunités ajoutées au pipeline.",
                    state="complete",
                )


# ==========================================
# ONGLET 2 : SCANNER UNE LISTE D'ENTREPRISES
# ==========================================
with tab2:
    st.subheader("Audit ciblé d'une liste d'entreprises suisses")
    st.caption(
        "Colle tes cibles prioritaires (1 par ligne) : l'outil scanne leur actu récente, "
        "choisit le bon CV et extrait les décideurs."
    )

    default_targets = (
        "Romande Energie\nAlpiq\nClimeworks\nCSEM\nGESDA\nQuantis\nSwissmem\nHitachi Energy Switzerland"
    )
    targets_text = st.text_area(
        "Liste des organisations (1 par ligne)", value=default_targets, height=180
    )
    role_filter = st.text_input(
        "Titres de décideurs recherchés sur LinkedIn",
        value='("Head of Public Affairs" OR "Head of Partnerships" OR "Strategy" OR "Head of Innovation" OR "Director" OR "HR")',
    )

    if st.button("🎯 Scanner cette liste", type="primary"):
        if not openai_key or not serper_key:
            st.error("Vérifie `OPENAI_API_KEY` et `SERPER_API_KEY` dans les Secrets Streamlit.")
        else:
            companies = [c.strip() for c in targets_text.splitlines() if c.strip()]
            progress = st.progress(0)
            for i, comp in enumerate(companies):
                st.write(f"🔍 Analyse de **{comp}**...")
                news = serper_search(
                    serper_key,
                    f'"{comp}" (Switzerland OR Suisse)',
                    search_type="news",
                    lang="en",
                    time_range="qdr:y",
                    num=3,
                )
                if not news:
                    news = serper_search(
                        serper_key,
                        f'"{comp}" actualité OR partenariat OR stratégie',
                        search_type="search",
                        lang="fr",
                        num=2,
                    )

                if news:
                    top = news[0]
                    combined_snippets = " | ".join(
                        [f"{n.get('title', '')}: {n.get('snippet', '')}" for n in news[:3]]
                    )
                    try:
                        analysis = analyze_opportunity(
                            openai_key,
                            st.session_state.cv_profiles,
                            top.get("title", comp),
                            combined_snippets,
                            top.get("source", "Web"),
                            company_hint=comp,
                            model=model_choice,
                        )
                        domain = find_company_domain(serper_key, comp)
                        contacts = find_decision_makers(serper_key, comp, role_filter, domain)

                        record = {
                            "company_name": comp,
                            "domain": domain,
                            "canton_or_city": analysis.get("canton_or_city", "Suisse"),
                            "segment": "Liste ciblée",
                            "signal_title": top.get("title", ""),
                            "signal_url": top.get("link", f"https://{domain}"),
                            "signal_date": top.get("date", "Récent"),
                            "hiring_score": int(analysis.get("hiring_score", 50)),
                            "recommended_cv": analysis.get("recommended_cv", ""),
                            "language": analysis.get("language", "EN"),
                            "target_role": analysis.get("target_role", ""),
                            "rationale": analysis.get("rationale", ""),
                            "contacts": contacts,
                            "draft_email_subject": analysis.get("draft_email_subject", ""),
                            "draft_email_body": analysis.get("draft_email_body", ""),
                            "draft_linkedin_msg": analysis.get("draft_linkedin_msg", ""),
                            "status": "À contacter",
                        }
                        save_opportunity(sb, record)
                    except Exception as e:
                        st.warning(f"Erreur sur {comp} : {e}")
                progress.progress((i + 1) / len(companies))
            st.success("Audit terminé ! Consulte l'onglet 'Pipeline & Candidatures'.")


# ==========================================
# ONGLET 3 : PIPELINE, CONTACTS & EMAILS
# ==========================================
with tab3:
    opps = load_opportunities(sb)
    if not opps:
        st.info("Aucune opportunité enregistrée pour l'instant. Lance un scan dans l'onglet 1 ou 2.")
    else:
        df = pd.DataFrame(opps)
        f1, f2, f3 = st.columns(3)
        with f1:
            cv_filter = st.multiselect(
                "Filtrer par CV recommandé", sorted(df["recommended_cv"].dropna().unique())
            )
        with f2:
            score_cut = st.slider("Score min affiché", 0, 100, 50)
        with f3:
            csv_export = (
                df.drop(columns=["contacts"], errors="ignore").to_csv(index=False).encode("utf-8")
            )
            st.download_button(
                "⬇️ Exporter en CSV",
                csv_export,
                "swiss_opportunities.csv",
                "text/csv",
                use_container_width=True,
            )

        filtered = [
            o
            for o in opps
            if o.get("hiring_score", 0) >= score_cut
            and (not cv_filter or o.get("recommended_cv") in cv_filter)
        ]

        st.markdown(f"**{len(filtered)} opportunités affichées**")

        for idx, opp in enumerate(filtered):
            badge = (
                "🟢"
                if opp["hiring_score"] >= 75
                else "🟡" if opp["hiring_score"] >= 55 else "⚪"
            )
            header = (
                f"{badge} {opp['hiring_score']}/100 | **{opp['company_name']}** "
                f"({opp.get('canton_or_city', '')}) — CV : `{opp['recommended_cv']}` ({opp['language']})"
            )
            with st.expander(header, expanded=(idx == 0)):
                c1, c2 = st.columns([1.2, 1])
                with c1:
                    st.markdown(f"**Poste probable à proposer :** {opp.get('target_role', '')}")
                    st.markdown(
                        f"**Signal détecté ({opp.get('signal_date', '')}) :** "
                        f"[{opp.get('signal_title', '')}]({opp.get('signal_url', '')})"
                    )
                    st.info(opp.get("rationale", ""))

                    st.markdown("#### 👥 Décideurs identifiés")
                    contacts = opp.get("contacts") or []
                    if not contacts:
                        st.caption(
                            "Aucun décideur extrait automatiquement (baisse le score min dans la sidebar ou vérifie le nom de l'entreprise)."
                        )
                    for ct in contacts:
                        emails_str = ", ".join(ct.get("guessed_emails", [])) or "Domaine non vérifié"
                        st.markdown(
                            f"- **{ct.get('name')}** — *{ct.get('role')}*  \n"
                            f"  🔗 [Profil LinkedIn]({ct.get('linkedin_url')}) | ✉️ `{emails_str}`"
                        )

                with c2:
                    st.markdown("#### ✉️ Email de candidature spontanée")
                    st.text_input(
                        "Objet", value=opp.get("draft_email_subject", ""), key=f"subj_{idx}"
                    )
                    st.text_area(
                        "Corps du mail",
                        value=opp.get("draft_email_body", ""),
                        height=220,
                        key=f"body_{idx}",
                    )
                    st.markdown("#### 💬 Note LinkedIn (<300 car.)")
                    st.code(opp.get("draft_linkedin_msg", ""), language=None)


# ==========================================
# ONGLET 4 : GESTION / MISE À JOUR DES 5 CV
# ==========================================
with tab4:
    st.subheader("Profils des 5 CV intégrés dans le moteur de matching")
    st.caption(
        "Les 5 CV sont pré-encodés. Tu peux ajuster leurs résumés ou uploader un PDF mis à jour."
    )

    for cv_id, data in st.session_state.cv_profiles.items():
        with st.expander(f"📄 {cv_id} — {data['filename']} ({data['lang']})"):
            new_summary = st.text_area(
                "Résumé utilisé par OpenAI",
                value=data["summary"],
                key=f"sum_{cv_id}",
                height=110,
            )
            new_best = st.text_input(
                "Cibles prioritaires", value=data["best_for"], key=f"best_{cv_id}"
            )
            uploaded = st.file_uploader(
                f"Remplacer le texte depuis un PDF ({cv_id})",
                type="pdf",
                key=f"pdf_{cv_id}",
            )
            if uploaded:
                reader = PdfReader(uploaded)
                extracted = "\n".join([page.extract_text() or "" for page in reader.pages])
                st.session_state.cv_profiles[cv_id]["summary"] = extracted[:3000]
                st.success("Texte extrait du PDF et injecté dans le moteur IA.")
            else:
                st.session_state.cv_profiles[cv_id]["summary"] = new_summary
                st.session_state.cv_profiles[cv_id]["best_for"] = new_best