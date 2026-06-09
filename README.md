# SEO Agent

An SEO intelligence system for [Claude Code](https://claude.com/claude-code). Point it at your domain and it:

- 🔍 **Finds your gap-zone keywords** — the ones stuck at positions 5–20 where one good article wins page 1
- 🏆 **Maps who's outranking you and why** — with threat levels and specific, non-generic reasons
- ✍️ **Generates a weekly content plan + drafts** in your brand voice
- 📊 **Builds an HTML dashboard** of the week's intelligence

It replaces a stack of $400–600/month SEO tools with a system that does the work, not just shows you data. Powered by Google Search Console (free) and Claude Code.

> **Built by [Robin Laseur](https://www.linkedin.com/in/robin-laseur-78576a40).** Free to use and share.

## Try it now — no credentials needed

This repo comes **pre-loaded with a fictional example** (Gymshark) so you can see exactly what it produces. The reports, drafts, and dashboard are already in `reports/` and `drafts/`. Open `reports/dashboard-2026-06-07.html` in a browser to see the output.

To regenerate it yourself from the sample data (no Google account needed), the `--demo` flag reads from `fixtures/`:

```bash
python scripts/gap_finder.py --demo
python scripts/competitor_intel.py --demo
python scripts/content_plan.py
python scripts/build_dashboard.py
python scripts/write_article.py --keyword "squat proof leggings"
```

## Use it on your own site

1. `pip install -r requirements.txt`
2. Set up Google Search Console OAuth and copy `.env.example` → `.env` (see [SETUP.md](SETUP.md))
3. Replace `brand-voice.md` with your brand (or run the brand interview — see `skills/brand-writer.md`), and clear out the sample files in `reports/` and `drafts/`
4. In Claude Code, say: **"Run the full weekly workflow"**

## How it's structured

| Path | What it is |
|------|------------|
| `skills/` | Instruction files Claude reads before acting (gap finder, competitor intel, brand writer) |
| `scripts/` | The Python that does the work |
| `fixtures/` | Sample GSC + SERP data that powers the `--demo` flag |
| `reports/` | Weekly outputs (`.md` + `.json`) — pre-loaded with the Gymshark example |
| `drafts/` | Article drafts — pre-loaded with the Gymshark example |
| `brand-voice.md` | Brand voice profile (currently the fictional Gymshark example) |
| `CLAUDE.md` | Project context loaded by Claude Code each session |
