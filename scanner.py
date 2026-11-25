import re
import unicodedata
from urllib.parse import urlparse

import dns.resolver
import requests
import streamlit as st


def serper_search(
    api_key: str,
    query: str,
    search_type: str = "news",
    lang: str = "fr",
    time_range: str = "qdr:m",
    num: int = 10,
) -> list:
    """Appelle Serper.dev (/news ou /search) ciblé sur la Suisse (gl=ch)."""
    url = f"https://google.serper.dev/{search_type}"
    clean_key = (api_key or "").strip().strip('"').strip("'")
    headers = {"X-API-KEY": clean_key, "Content-Type": "application/json"}
    payload = {
        "q": query,
        "gl": "ch",
        "hl": lang,
        "num": int(num),
    }
    if search_type == "news" and time_range:
        payload["tbs"] = time_range

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
    except requests.RequestException as e:
        st.error(f"Erreur réseau Serper ({search_type}) : {e}")
        return []

    if not resp.ok:
        st.error(f"Erreur Serper ({resp.status_code}) sur `{search_type}` : {resp.text}")
        return []

    data = resp.json()
    return data.get("news", []) if search_type == "news" else data.get("organic", [])


def find_company_domain(api_key: str, company_name: str) -> str:
    """Trouve le nom de domaine officiel d'une organisation suisse."""
    results = serper_search(
        api_key,
        f'"{company_name}" Switzerland official website',
        search_type="search",
        lang="en",
        num=3,
    )
    excluded = [
        "linkedin.com",
        "wikipedia.org",
        "zefix.ch",
        "moneyhouse.ch",
        "northdata",
        "bloomberg.com",
        "crunchbase.com",
    ]
    for item in results:
        link = item.get("link", "")
        domain = urlparse(link).netloc.replace("www.", "")
        if domain and not any(ex in domain for ex in excluded):
            return domain
    return ""


def check_mx_valid(domain: str) -> bool:
    """Vérifie gratuitement si le domaine accepte les emails (enregistrement MX)."""
    if not domain:
        return False
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=3)
        return len(answers) > 0
    except Exception:
        return False


def _normalize_name(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"[^a-z]", "", text.lower())


def guess_emails(full_name: str, domain: str) -> list:
    """Génère les formats d'emails professionnels suisses les plus probables."""
    if not domain or not full_name:
        return []
    parts = [p for p in re.split(r"[\s\-]+", full_name.strip()) if len(p) > 1]
    if len(parts) < 2:
        return []
    first = _normalize_name(parts[0])
    last = _normalize_name(parts[-1])
    if not first or not last:
        return []
    return [
        f"{first}.{last}@{domain}",
        f"{first[0]}.{last}@{domain}",
        f"{first}{last}@{domain}",
    ]


def find_decision_makers(
    api_key: str, company_name: str, role_query: str, domain: str = ""
) -> list:
    """Trouve 2 à 4 décideurs clés sur LinkedIn Suisse via Google Dork."""
    dork = (
        f'site:linkedin.com/in/ "{company_name}" '
        f"(Switzerland OR Suisse OR Lausanne OR Geneva OR Zurich OR Bern) {role_query}"
    )
    results = serper_search(api_key, dork, search_type="search", lang="en", num=5)

    if not results:
        dork_broad = (
            f'site:linkedin.com/in/ "{company_name}" '
            f"(Switzerland OR Suisse) (Director OR Head OR Manager OR CEO OR HR)"
        )
        results = serper_search(
            api_key, dork_broad, search_type="search", lang="en", num=4
        )

    mx_ok = check_mx_valid(domain) if domain else False
    contacts = []
    seen_urls = set()

    for r in results:
        link = r.get("link", "")
        if link in seen_urls:
            continue
        seen_urls.add(link)

        title_raw = r.get("title", "")
        clean_title = re.sub(r"\s*\|\s*LinkedIn.*$", "", title_raw)
        parts = [p.strip() for p in re.split(r"\s+[-–|]\s+", clean_title)]
        name = parts[0] if parts else clean_title
        role = parts[1] if len(parts) > 1 else r.get("snippet", "")[:120]

        contacts.append(
            {
                "name": name,
                "role": role,
                "linkedin_url": link,
                "guessed_emails": guess_emails(name, domain) if mx_ok else [],
                "mx_verified": mx_ok,
            }
        )
    return contacts[:4]