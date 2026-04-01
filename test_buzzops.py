"""
BuzzOps test program — exercises all four tools with sample inputs.
Run with: python test_buzzops.py
"""

import json
from buzzops.server import debuzz, retro_halo, countdown_to_zombie, investor_combustion

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"


def header(title: str):
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}")


def section(label: str, value):
    print(f"{YELLOW}{label}:{RESET} {value}")


def show_translations(translations: list):
    if not translations:
        print(f"  {RED}(none matched){RESET}")
        return
    for t in translations:
        print(f"  {BOLD}[{t['buzzword']}]{RESET}")
        print(f"    WHAT THEY SAY: {t['they_say']}")
        print(f"    {GREEN}WHAT THEY MEAN: {t['they_mean']}{RESET}")


# ---------------------------------------------------------------------------
# Test 1 — AI Debuzzer™ with pasted text
# ---------------------------------------------------------------------------

header("TEST 1 — AI Debuzzer™ (pasted text)")

sample_text = (
    "We are an agentic, AI-native, context-engineered semantic intelligence fabric "
    "for governed real-time decisioning at enterprise scale. Our composable data product "
    "platform empowers modern data teams to democratize actionable insights with "
    "frictionless observability and data contracts. With our lakehouse architecture and "
    "shift-left quality approach, your AI-ready governance journey starts here."
)

print(f"\nInput:\n  {sample_text}\n")

result = json.loads(debuzz(sample_text))
section("Buzzword density", f"{result['buzzword_density_pct']}% ({result['total_buzzwords_found']} buzzwords in {result['total_words']} words)")
section("Top offenders", ", ".join(result["top_offenders"].keys()))
print(f"\n{BOLD}Known translations from the BuzzOps field guide:{RESET}")
show_translations(result["known_translations"])

# ---------------------------------------------------------------------------
# Test 2 — AI Debuzzer™ with a URL
# ---------------------------------------------------------------------------

header("TEST 2 — AI Debuzzer™ (URL fetch)")

url = "https://www.databricks.com/product/data-lakehouse"
print(f"\nFetching: {url}\n")

try:
    result = json.loads(debuzz(url))
    section("Source", result["source"])
    section("Buzzword density", f"{result['buzzword_density_pct']}%")
    section("Top offenders", ", ".join(list(result["top_offenders"].keys())[:5]))
    print(f"\n{BOLD}Known translations:{RESET}")
    show_translations(result["known_translations"])
except Exception as e:
    print(f"{RED}Fetch failed (network?): {e}{RESET}")

# ---------------------------------------------------------------------------
# Test 3 — RetroHalo™
# ---------------------------------------------------------------------------

header("TEST 3 — RetroHalo™ (company rebrand archaeology)")

company = "Monte Carlo Data"
print(f"\nCompany: {company}\n")

result = json.loads(retro_halo(company))
print(f"{BOLD}Current messaging snippets:{RESET}")
for item in result["current_messaging"][:2]:
    print(f"  [{item['title']}]")
    print(f"  {item['snippet'][:200]}...")
    print()

print(f"{BOLD}Old messaging (2022-2023):{RESET}")
for item in result["old_messaging_2022_2023"][:2]:
    print(f"  [{item['title']}]")
    print(f"  {item['snippet'][:200]}...")
    print()

# ---------------------------------------------------------------------------
# Test 4 — Countdown to Zombie™
# ---------------------------------------------------------------------------

header("TEST 4 — Countdown to Zombie™")

company = "Atlan"
print(f"\nCompany: {company}\n")

result = json.loads(countdown_to_zombie(company))
print(f"{BOLD}Funding signals:{RESET}")
for item in result["funding_signals"][:2]:
    print(f"  {item['snippet'][:200]}")
print()

print(f"{BOLD}Distress signals:{RESET}")
for item in result["distress_signals"][:2]:
    if item["snippet"]:
        print(f"  {item['snippet'][:200]}")
print()

bw = result["buzzword_density_in_signals"]
if bw:
    top = sorted(bw.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"{BOLD}Buzzwords in all signals:{RESET} {dict(top)}")

# ---------------------------------------------------------------------------
# Test 5 — Investor Combustion Model™
# ---------------------------------------------------------------------------

header("TEST 5 — Investor Combustion Model™")

company = "Collibra"
print(f"\nCompany: {company}\n")

result = json.loads(investor_combustion(company))
section("Marketing buzzword density", f"{result['marketing_buzzword_density_pct']}%")
section("Real-user buzzword density", f"{result['user_buzzword_density_pct']}%")
delta = round(result["marketing_buzzword_density_pct"] - result["user_buzzword_density_pct"], 1)
section("Gap (marketing vs users)", f"{delta}pp {'(high BS differential)' if delta > 5 else '(roughly honest)'}")
print(f"\n{BOLD}Top marketing buzzwords:{RESET}")
for bw, count in list(result["top_marketing_buzzwords"].items())[:5]:
    print(f"  {bw}: {count}")

print(f"\n{BOLD}{GREEN}All tests complete.{RESET}")
