"""
BuzzOps MCP Server
==================
The industry's first open-source, agentic, reactive, context-engineered,
AI-native, semantics-first, shift-left, vendor-agnostic, cloud-flexible
buzzword operations platform for modern data teams.

Translation: it tells you what vendors actually do.
"""

import re
import json
from urllib.parse import urlparse, quote_plus

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "BuzzOps",
    instructions=(
        "You are BuzzOps, a brutally honest translator of enterprise software marketing. "
        "When using these tools, your job is to cut through buzzword soup and tell people "
        "what vendors actually do. Be witty, precise, and merciless. "
        "Replace phrases like 'agentic semantic intelligence fabric' with what they mean: "
        "'we added AI to our dashboard copy.' "
        "You have four tools: debuzz, retro_halo, countdown_to_zombie, investor_combustion."
    ),
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

BUZZWORDS = [
    "agentic", "AI-native", "AI native", "context-aware", "context aware",
    "context engineering", "context-engineered", "semantic", "semantics-first",
    "semantics first", "composable", "observable", "observability", "lakehouse",
    "data mesh", "data fabric", "data product", "data products", "data contract",
    "data contracts", "shift left", "shift-left", "governed", "governance",
    "intelligent", "intelligent automation", "autonomous", "autonomously",
    "real-time", "real time", "decisioning", "intelligence fabric",
    "copilot", "co-pilot", "next-generation", "next generation", "modern",
    "enterprise-grade", "enterprise grade", "cloud-native", "cloud native",
    "multi-cloud", "multicloud", "hyper-scale", "hyperscale", "purpose-built",
    "purpose built", "end-to-end", "end to end", "best-in-class", "best in class",
    "cutting-edge", "cutting edge", "digital transformation", "disruptive",
    "revolutionary", "game-changing", "game changing", "paradigm", "ecosystem",
    "synergy", "synergistic", "leverage", "scalable", "robust", "seamless",
    "frictionless", "holistic", "proactive", "reactive", "transformative",
    "innovative", "industry-leading", "world-class", "unified platform",
    "single pane of glass", "360-degree", "360 degree", "data-driven",
    "data driven", "insights", "actionable insights", "democratize",
    "empower", "reimagine", "reinvent", "rethink", "reimagined",
]


# ---------------------------------------------------------------------------
# Canonical buzzword translation table (from the BuzzOps field guide)
# Keys are lowercase for case-insensitive matching.
# ---------------------------------------------------------------------------

BUZZWORD_TRANSLATIONS = {
    "context engineering": {
        "they_say": "We make AI understand your business context.",
        "they_mean": (
            "They feed the model enough metadata and examples that it stops "
            "free associating like a guy three coffees deep at a whiteboard."
        ),
    },
    "agentic analytics": {
        "they_say": "Autonomous agents reason over your data and take action.",
        "they_mean": (
            "It is a chatbot with tool access and the confidence of a summer intern."
        ),
    },
    "agentic": {
        "they_say": "Autonomous agents reason over your data and take action.",
        "they_mean": (
            "It is a chatbot with tool access and the confidence of a summer intern."
        ),
    },
    "data contracts": {
        "they_say": "Governed producer consumer reliability at scale.",
        "they_mean": (
            "They want upstream teams to stop breaking things and acting surprised."
        ),
    },
    "data contract": {
        "they_say": "Governed producer consumer reliability at scale.",
        "they_mean": (
            "They want upstream teams to stop breaking things and acting surprised."
        ),
    },
    "shift left": {
        "they_say": "Quality embedded early in the lifecycle.",
        "they_mean": (
            "Catch the problem before it reaches the CEO's dashboard and ruins everyone's afternoon."
        ),
    },
    "shift-left": {
        "they_say": "Quality embedded early in the lifecycle.",
        "they_mean": (
            "Catch the problem before it reaches the CEO's dashboard and ruins everyone's afternoon."
        ),
    },
    "ai observability": {
        "they_say": "Full stack monitoring for intelligent systems.",
        "they_mean": (
            "The model is doing weird stuff in production, and now they need logs with better branding."
        ),
    },
    "observability": {
        "they_say": "Full stack monitoring for intelligent systems.",
        "they_mean": (
            "The model is doing weird stuff in production, and now they need logs with better branding."
        ),
    },
    "data products": {
        "they_say": "Domain-owned reusable analytical assets.",
        "they_mean": "They put an owner, an SLA, and a roadmap on a table.",
    },
    "data product": {
        "they_say": "Domain-owned reusable analytical assets.",
        "they_mean": "They put an owner, an SLA, and a roadmap on a table.",
    },
    "lakehouse": {
        "they_say": "A unified architecture for all enterprise workloads.",
        "they_mean": (
            "It is storage, compute, and a very determined marketing team. Oh, and buy Databricks."
        ),
    },
    "mcp": {
        "they_say": "A standard protocol for model tool interoperability.",
        "they_mean": "A cleaner way to plug an LLM into stuff.",
    },
    "ai-ready governance": {
        "they_say": "Responsible innovation with trusted enterprise controls.",
        "they_mean": "Same governance meeting. New deck. More panic.",
    },
    "governance": {
        "they_say": "Responsible innovation with trusted enterprise controls.",
        "they_mean": "Same governance meeting. New deck. More panic.",
    },
}


def _match_translations(text: str) -> list[dict]:
    """Return translation entries for every known buzzword found in text."""
    text_lower = text.lower()
    seen = set()
    matches = []
    # Sort longest keys first so "agentic analytics" matches before "agentic"
    for key in sorted(BUZZWORD_TRANSLATIONS, key=len, reverse=True):
        if key in text_lower and key not in seen:
            entry = BUZZWORD_TRANSLATIONS[key].copy()
            entry["buzzword"] = key
            matches.append(entry)
            # Mark sub-phrases as seen to avoid duplicate entries
            for other_key in BUZZWORD_TRANSLATIONS:
                if other_key in key:
                    seen.add(other_key)
            seen.add(key)
    return matches


def _count_buzzwords(text: str) -> dict:
    text_lower = text.lower()
    found = {}
    for bw in BUZZWORDS:
        count = text_lower.count(bw.lower())
        if count:
            found[bw] = count
    return found


def _fetch_url(url: str, timeout: int = 15) -> str:
    """Fetch a URL and return visible text content."""
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=timeout) as client:
        resp = client.get(url)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:8000]  # cap to avoid flooding context


def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """DuckDuckGo text search, returns list of {title, href, body}."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return [{"title": "Search error", "href": "", "body": str(exc)}]


def _is_url(text: str) -> bool:
    try:
        result = urlparse(text.strip())
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Tool 1 — AI Debuzzer™
# ---------------------------------------------------------------------------

@mcp.tool()
def debuzz(content: str) -> str:
    """AI Debuzzer™ — Point this at any product page URL, LinkedIn post, keynote
    transcript, analyst report, or raw text. It returns the source material
    with a buzzword density report so you can translate it into plain English.

    Pass either:
      - A URL (https://...) — the page will be fetched and parsed
      - Raw text — pasted directly from a deck, doc, or LinkedIn sermon

    After calling this tool, analyze the returned content and rewrite the
    marketing claims as a brutally honest plain-English description of what
    the company actually does. Format the output as:

      WHAT THEY SAY: [original claim]
      WHAT THEY MEAN: [plain English translation]

    Repeat for the top 3-5 most egregious claims. Then add a one-sentence
    TL;DR at the end.
    """
    if _is_url(content):
        try:
            raw_text = _fetch_url(content)
            source_label = f"URL: {content}"
        except Exception as exc:
            return f"Could not fetch {content}: {exc}"
    else:
        raw_text = content.strip()[:8000]
        source_label = "Pasted text"

    bw_counts = _count_buzzwords(raw_text)
    total_bw = sum(bw_counts.values())
    total_words = len(raw_text.split())
    density_pct = round(total_bw / max(total_words, 1) * 100, 1)

    top_buzzwords = sorted(bw_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    known_translations = _match_translations(raw_text)

    return json.dumps({
        "source": source_label,
        "buzzword_density_pct": density_pct,
        "total_buzzwords_found": total_bw,
        "total_words": total_words,
        "top_offenders": dict(top_buzzwords),
        "known_translations": known_translations,
        "raw_content": raw_text,
        "instruction": (
            "Use the entries in known_translations as authoritative WHAT THEY SAY / WHAT THEY MEAN "
            "pairs — these come directly from the BuzzOps field guide and should be returned verbatim. "
            "For any buzzwords in top_offenders not covered by known_translations, write your own "
            "plain-English translation in the same style. "
            "Present all translations in the format:\n"
            "  BUZZWORD: [term]\n"
            "  WHAT THEY SAY: [marketing claim]\n"
            "  WHAT THEY MEAN: [plain English]\n"
            "End with a one-sentence TL;DR of the whole piece."
        ),
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 2 — RetroHalo™
# ---------------------------------------------------------------------------

@mcp.tool()
def retro_halo(company_name: str) -> str:
    """RetroHalo™ — Compares what a vendor says today vs. what they said 18 months
    ago, before they discovered they had always been 'agentic' somehow.

    Pass the company name (e.g. 'Databricks', 'dbt Labs', 'Monte Carlo').
    This tool searches for their current positioning AND archived/old descriptions,
    then returns both so you can surface the rebrand archaeology.

    After calling this tool, identify the most dramatic repositioning and deliver
    it in the style of:
      "In [month year], you called this a [old description].
       Now you call it an [new buzzword salad]. No drama. Just archaeology."
    """
    current_results = _ddg_search(
        f"{company_name} data platform what we do site:linkedin.com OR site:{_slug(company_name)}.com",
        max_results=3,
    )
    old_results = _ddg_search(
        f"{company_name} data platform 2023 OR 2022 description \"we are\" OR \"we help\"",
        max_results=3,
    )
    wayback_results = _ddg_search(
        f"site:web.archive.org {company_name}.com 2023",
        max_results=2,
    )

    return json.dumps({
        "company": company_name,
        "current_messaging": [
            {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
            for r in current_results
        ],
        "old_messaging_2022_2023": [
            {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
            for r in old_results
        ],
        "wayback_links": [
            {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
            for r in wayback_results
        ],
        "instruction": (
            "Compare the old vs new messaging. Identify the biggest repositioning. "
            "Deliver it as: 'In [period], you called this [old plain description]. "
            "Now you call it [new buzzword string]. No drama. Just archaeology.'"
        ),
    }, indent=2)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower().replace(" ", ""))


# ---------------------------------------------------------------------------
# Tool 3 — Countdown to Zombie™
# ---------------------------------------------------------------------------

@mcp.tool()
def countdown_to_zombie(company_name: str) -> str:
    """Countdown to Zombie™ — Estimates when a startup's remaining life force will
    be fully converted into LinkedIn content and webinars.

    Tracks: funding rounds (when was the last one?), LinkedIn post velocity,
    employee buzzword density, job posting patterns (are they hiring salespeople
    or engineers?), and general desperation signals.

    Pass a company name. This tool gathers signals from the web and returns
    structured data. After calling this tool, produce:
      - A Zombie Probability Score (0-100%)
      - Estimated quarters until full conversion to 'webinar series with payroll'
      - Top 3 warning signs observed
      - One-line verdict
    """
    funding_results = _ddg_search(
        f"{company_name} funding round raised million 2024 OR 2025",
        max_results=3,
    )
    linkedin_results = _ddg_search(
        f"{company_name} linkedin site:linkedin.com company",
        max_results=2,
    )
    jobs_results = _ddg_search(
        f"{company_name} jobs hiring site:greenhouse.io OR site:lever.co OR site:careers",
        max_results=3,
    )
    news_results = _ddg_search(
        f"{company_name} layoffs OR pivot OR rebrand OR acquisition 2024 OR 2025",
        max_results=3,
    )

    all_snippets = " ".join(
        r.get("body", "") for r in funding_results + linkedin_results + jobs_results + news_results
    )
    bw_density = _count_buzzwords(all_snippets)

    return json.dumps({
        "company": company_name,
        "funding_signals": [
            {"title": r.get("title"), "snippet": r.get("body"), "url": r.get("href")}
            for r in funding_results
        ],
        "linkedin_presence": [
            {"title": r.get("title"), "snippet": r.get("body")}
            for r in linkedin_results
        ],
        "hiring_signals": [
            {"title": r.get("title"), "snippet": r.get("body")}
            for r in jobs_results
        ],
        "distress_signals": [
            {"title": r.get("title"), "snippet": r.get("body")}
            for r in news_results
        ],
        "buzzword_density_in_signals": bw_density,
        "instruction": (
            "Based on these signals, produce: "
            "(1) Zombie Probability Score 0-100%, "
            "(2) Estimated quarters until full conversion to 'webinar series with payroll', "
            "(3) Top 3 warning signs, "
            "(4) One-line verdict. Be darkly funny but grounded in the actual evidence."
        ),
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 4 — Investor Combustion Model™
# ---------------------------------------------------------------------------

@mcp.tool()
def investor_combustion(company_name: str) -> str:
    """Investor Combustion Model™ — Measures how quickly venture capital is being
    transformed into adjectives.

    Analyzes: total funding raised, estimated headcount, LinkedIn post frequency,
    buzzwords per post, product clarity signals, analyst mentions vs. real user
    mentions, and the funding-to-clarity ratio.

    Pass a company name. After calling this tool, compute and report:
      - The Combustion Ratio (dollars raised per coherent product sentence)
      - Adjective Velocity (buzzwords generated per dollar of VC)
      - Answer: 'Is this a product, or $X million trapped inside a synonym generator?'
      - Prognosis: 'How many quarters until this becomes a content strategy with a logo?'
    """
    funding_results = _ddg_search(
        f"{company_name} total funding raised valuation crunchbase OR pitchbook",
        max_results=3,
    )
    product_results = _ddg_search(
        f"{company_name} product features pricing what does it do",
        max_results=3,
    )
    analyst_results = _ddg_search(
        f"{company_name} gartner OR forrester OR \"magic quadrant\" OR analyst",
        max_results=2,
    )
    user_review_results = _ddg_search(
        f"{company_name} review site:g2.com OR site:gartner.com/reviews OR reddit",
        max_results=3,
    )

    all_marketing = " ".join(r.get("body", "") for r in product_results + analyst_results)
    all_user_voice = " ".join(r.get("body", "") for r in user_review_results)

    marketing_bw = _count_buzzwords(all_marketing)
    user_bw = _count_buzzwords(all_user_voice)

    marketing_bw_total = sum(marketing_bw.values())
    user_bw_total = sum(user_bw.values())
    marketing_words = len(all_marketing.split()) or 1
    user_words = len(all_user_voice.split()) or 1

    return json.dumps({
        "company": company_name,
        "funding_data": [
            {"title": r.get("title"), "snippet": r.get("body")}
            for r in funding_results
        ],
        "product_clarity_signals": [
            {"title": r.get("title"), "snippet": r.get("body")}
            for r in product_results
        ],
        "analyst_coverage": [
            {"title": r.get("title"), "snippet": r.get("body")}
            for r in analyst_results
        ],
        "real_user_reviews": [
            {"title": r.get("title"), "snippet": r.get("body")}
            for r in user_review_results
        ],
        "marketing_buzzword_density_pct": round(marketing_bw_total / marketing_words * 100, 1),
        "user_buzzword_density_pct": round(user_bw_total / user_words * 100, 1),
        "top_marketing_buzzwords": dict(
            sorted(marketing_bw.items(), key=lambda x: x[1], reverse=True)[:8]
        ),
        "instruction": (
            "Based on this data compute and report: "
            "(1) Combustion Ratio: dollars raised per coherent product sentence (estimate from signals), "
            "(2) Adjective Velocity: buzzwords generated per dollar of VC, "
            "(3) Answer the question: 'Is this a product, or $X million trapped inside a synonym generator?' "
            "(4) Prognosis: quarters until this becomes a content strategy with a logo. "
            "Be precise, darkly comic, and grounded in the evidence."
        ),
    }, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    mcp.run()


if __name__ == "__main__":
    main()
