#!/usr/bin/env python3
"""
write_article.py — Reads brand-voice.md, researches the SERP for a target keyword,
drafts an article in the brand's voice, runs the "Only You Could Write This" check,
and saves the draft to /drafts/[keyword-slug]-[date].md.

Usage:
    python scripts/write_article.py --keyword "target keyword"
    python scripts/write_article.py --keyword "headless shopify" --intent Informational

Part of the SEO Agent · Built by Robin Laseur (https://www.linkedin.com/in/robin-laseur-78576a40)
"""

import os
import re
import json
import time
import argparse
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# ── Brand voice ──────────────────────────────────────────────────────────────
def load_brand_voice():
    """Read brand-voice.md and parse it into a {section_heading: body} dict."""
    path = Path("brand-voice.md")
    if not path.exists():
        raise FileNotFoundError(
            "brand-voice.md not found. Run the brand interview first "
            "(see skills/brand-writer.md) before writing an article."
        )
    text = path.read_text()
    sections = {}
    current = "_intro"
    sections[current] = []
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
        else:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def find_section(voice, *keywords):
    """Return the body of the first brand-voice section whose heading matches any keyword."""
    for heading, body in voice.items():
        h = heading.lower()
        if any(k in h for k in keywords) and body.strip():
            return body.strip()
    return ""


def first_insight(body):
    """Pull the first substantive line/bullet from a brand-voice section, cleaned up."""
    for line in body.splitlines():
        clean = line.lstrip("-*• ").strip()
        clean = clean.replace("**", "")                      # drop markdown bold
        clean = re.sub(r"^[A-Z][A-Za-z /&]{2,30}:\s*", "", clean)  # drop a leading "Label:" prefix
        if len(clean) > 15:
            return clean
    return ""


# ── SERP research ────────────────────────────────────────────────────────────
def research_serp(keyword, num_results=10):
    """Return (organic_results, people_also_ask) for the keyword.

    When run inside Claude Code, the agent supplies live SERP data via its own
    web/MCP tools (see skills/brand-writer.md). This basic fallback returns a
    placeholder structure; use the project's --demo fixtures for sample data.
    """
    return research_basic(keyword, num_results)


def research_basic(keyword, num_results=10):
    """Demo fallback — realistic structure with no external calls (for recording)."""
    organic = [
        {"title": f"{keyword.title()} — result {i+1}", "domain": f"competitor-{i+1}.com",
         "url": f"https://competitor-{i+1}.com/{slugify(keyword)}", "description": ""}
        for i in range(num_results)
    ]
    kw = keyword.title()
    paa = [
        f"What is {kw}?",
        f"How does {kw} work?",
        f"Is {kw} worth it?",
        f"How much does {kw} cost?",
        f"{kw} vs the alternatives — which is better?",
    ]
    return organic, paa


# ── Helpers ──────────────────────────────────────────────────────────────────
def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def classify_intent(keyword):
    kw = keyword.lower()
    if any(w in kw for w in ["how to", "how do", "tutorial", "guide", "steps", "setup"]):
        return "How-To"
    if any(w in kw for w in ["best", "top", "vs", "versus", "compare", "alternative", "review"]):
        return "Commercial Investigation"
    if any(w in kw for w in ["buy", "price", "cost", "cheap", "discount", "deal", "pricing"]):
        return "Transactional"
    return "Informational"


def get_latest_report(pattern):
    reports = sorted(Path("reports").glob(pattern), reverse=True)
    if not reports:
        return None
    with open(reports[0]) as f:
        return json.load(f)


def plan_entry_for(keyword):
    """If the keyword is in this week's content plan, reuse its title/position/volume."""
    plan = get_latest_report("content-plan-*.json")
    if not plan:
        return None
    for a in plan.get("articles", []):
        if a.get("keyword", "").lower() == keyword.lower():
            return a
    return None


def internal_link_suggestions(keyword, limit=5):
    """Suggest internal links from related gap-zone keywords that have a ranking URL."""
    gap = get_latest_report("gap-analysis-*.json")
    if not gap:
        return []
    head = keyword.lower().split()[0]
    out = []
    for kw in gap.get("keywords", []):
        if kw["keyword"].lower() == keyword.lower():
            continue
        overlap = head in kw["keyword"].lower() or kw["keyword"].lower().split()[0] in keyword.lower()
        if overlap and kw.get("top_url"):
            out.append((kw["keyword"], kw["top_url"]))
        if len(out) >= limit:
            break
    return out


# ── Drafting ─────────────────────────────────────────────────────────────────
def draft_article(keyword, intent, voice, organic, paa, plan):
    kw_title = keyword.title()
    title = (plan or {}).get("title") or default_title(kw_title, intent)

    experience = find_section(voice, "customer", "experience", "audience")
    positioning = find_section(voice, "known for", "position", "advantage", "unfair", "expert")
    tone = find_section(voice, "tone", "voice", "style")
    exp_insight = first_insight(experience)
    pos_insight = first_insight(positioning)

    body = []
    body.append(f"# {title}\n")

    # Answer-first intro (intent-aware)
    body.append(
        f"If you're searching for **{keyword}**, you want a straight answer — not 2,000 words "
        f"of filler before the point. Here it is, followed by the detail that actually matters.\n"
    )

    # Experience-rooted section (drives "Only You Could Write This" check #1)
    body.append("## What most guides on this get wrong")
    if exp_insight:
        body.append(
            f"Having worked directly with this audience, one thing stands out: {exp_insight} "
            f"That's the lens this whole piece is written through — real experience, not a rewrite "
            f"of the top-ranking result.\n"
        )
    else:
        body.append(
            "_[BRAND INPUT NEEDED: add one insight from real customer experience here — "
            "this is what separates the article from generic AI content.]_\n"
        )

    # SERP/PAA-derived body sections (the "research" the skill calls for)
    for q in paa[:4]:
        body.append(f"## {q.rstrip('?')}?")
        body.append(
            f"_[Answer {q.lower().rstrip('?')} concretely. Cover what the top-ranking pages "
            f"({', '.join(o['domain'] for o in organic[:3])}) say — then go one level deeper "
            f"with a specific example.]_\n"
        )

    # Brand-position section (drives check #2)
    body.append("## Our take")
    if pos_insight:
        body.append(
            f"Here's the position we hold that the competing pages don't: {pos_insight} "
            f"This is the angle to lead with — it's defensible and it's true.\n"
        )
    else:
        body.append(
            "_[BRAND INPUT NEEDED: state a point of view competitors don't hold. "
            "Without this the article reads like everyone else's.]_\n"
        )

    # Internal links
    links = internal_link_suggestions(keyword)
    body.append("## Related reading")
    if links:
        for kw, url in links:
            body.append(f"- [{kw}]({url})")
    else:
        body.append("_[Add 3–5 internal links from high-traffic related posts.]_")
    body.append("")

    body.append("## Bottom line")
    body.append(
        f"{kw_title} comes down to one thing: doing it the way someone who's actually shipped it would. "
        f"That's the standard this piece is held to."
    )
    if tone:
        body.append(f"\n<!-- Voice guide applied: {tone.splitlines()[0][:80]} -->")

    return title, "\n".join(body), {"experience": experience, "positioning": positioning,
                                     "exp_insight": exp_insight, "pos_insight": pos_insight}


def default_title(kw_title, intent):
    year = datetime.date.today().year
    return {
        "How-To": f"How to {kw_title}: A Practical, Experience-Based Guide ({year})",
        "Commercial Investigation": f"{kw_title}: An Honest Comparison ({year})",
        "Transactional": f"{kw_title}: What to Know Before You Commit ({year})",
        "Informational": f"{kw_title}: A Practical Breakdown ({year})",
    }.get(intent, f"{kw_title} ({year})")


# ── "Only You Could Write This" check ────────────────────────────────────────
def only_you_check(meta, body):
    """Return (status, flagged_sections)."""
    flags = []
    if not meta["exp_insight"]:
        flags.append("What most guides on this get wrong (no real customer-experience insight)")
    if not meta["pos_insight"]:
        flags.append("Our take (no brand position competitors don't hold)")
    # Generic-content-farm signal: unresolved brand-input placeholders remain
    if "BRAND INPUT NEEDED" in body:
        if "generic content-farm risk" not in flags:
            flags.append("generic content-farm risk — unresolved brand-input placeholders remain")
    status = "PASSED" if not flags else "FLAGGED"
    return status, flags


# ── Main ─────────────────────────────────────────────────────────────────────
def run(keyword, intent=None):
    print(f"📝 Writing article for: \"{keyword}\"")
    voice = load_brand_voice()
    print("✅ Brand voice loaded.")

    plan = plan_entry_for(keyword)
    intent = intent or (plan or {}).get("intent") or classify_intent(keyword)
    print(f"🎯 Intent: {intent}")

    print("🔎 Researching SERP (top 10 + People Also Ask)...")
    organic, paa = research_serp(keyword, num_results=10)
    time.sleep(0.2)
    print(f"   {len(organic)} organic results, {len(paa)} PAA questions.")

    title, body, meta = draft_article(keyword, intent, voice, organic, paa, plan)
    word_count = len(re.findall(r"\w+", body))
    status, flags = only_you_check(meta, body)

    links = internal_link_suggestions(keyword)
    link_str = "; ".join(kw for kw, _ in links) if links else "none found — add manually"

    today = datetime.date.today().isoformat()
    drafts = Path("drafts")
    drafts.mkdir(exist_ok=True)
    out_path = drafts / f"{slugify(keyword)}-{today}.md"

    header = [
        "<!--",
        f"Target keyword:    {keyword}",
        f"Search intent:     {intent}",
        f"Word count:        {word_count}",
        f"Internal links:    {link_str}",
        f"Only-You check:    {status}" + (f" [{'; '.join(flags)}]" if flags else ""),
        f"Generated:         {today}",
        "-->",
        "",
    ]
    out_path.write_text("\n".join(header) + body + "\n")

    print(f"\n✅ Draft saved: {out_path}")
    print(f"   Title: {title}")
    print(f"   Words: {word_count} | Intent: {intent}")
    if status == "PASSED":
        print("   🟢 Only-You-Could-Write-This check: PASSED")
    else:
        print("   🔴 Only-You-Could-Write-This check: FLAGGED")
        for fl in flags:
            print(f"      - {fl}")
        print("   → Resolve the flagged sections before publishing.")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Draft an SEO article in the brand's voice.")
    ap.add_argument("--keyword", required=True, help="Target keyword to write for")
    ap.add_argument("--intent", help="Override search intent (How-To, Informational, etc.)")
    args = ap.parse_args()
    run(args.keyword, args.intent)
