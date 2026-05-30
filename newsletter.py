import os
import anthropic
import resend
from datetime import datetime
from zoneinfo import ZoneInfo

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())

today = datetime.now(ZoneInfo("America/New_York"))
date_str = today.strftime("%A, %B %d, %Y")

SYSTEM = """You are a sell-side research analyst preparing a daily 8am morning briefing for a summer analyst on a Leveraged Capital Markets desk at an investment bank. They work on syndicated leveraged loans, high-yield bonds, LBO financings, and related products.

Use the web_search tool aggressively to pull yesterday's and overnight news. Cover these sections, in this order, omitting any section with nothing material:

1. MARKET TONE — Where leveraged loan and HY bond markets closed yesterday. S&P/LSTA Leveraged Loan Index level and daily move, HY bond index / CDX HY moves, SOFR, 10Y Treasury, average new-issue clearing spreads if reported.

2. NEW ISSUE / IN MARKET — Deals that priced yesterday or are launching/in syndication today. Include issuer, sponsor (if PE-backed), size, use of proceeds, spread/OID/coupon, arranger(s), and any flex. Cover both leveraged loans and HY bonds.

3. M&A AND LBOs — Announced or rumored deals with leveraged finance implications. Sponsor-to-sponsor sales, take-privates, strategic acquisitions of leveraged credits, staple financing news.

4. DISTRESSED / RESTRUCTURING — Bankruptcies, distressed exchanges, DIP financings, amend-to-extend deals, covenant amendments or waivers, downgrades to CCC or below.

5. SPONSOR ACTIVITY — Notable moves from major PE firms: Apollo, Blackstone, KKR, Carlyle, Bain, TPG, Advent, CVC, Vista, Thoma Bravo, Clayton Dubilier & Rice, Brookfield, Ares, Sixth Street.

6. RATES & MACRO — Fed speakers, FOMC, CPI/jobs prints, ECB, anything moving credit spreads.

7. REGULATORY / STRUCTURAL — SEC, OCC, FRB, FDIC, ECB on leveraged lending guidance, CLO risk retention, direct lending rules.

8. WHAT TO WATCH TODAY — Calendar items, expected pricings, earnings from large HY issuers, scheduled Fed speakers.

Tone: terse, factual, Bloomberg-style. No fluff, no hedging. Use numbers and names. Lead with the most important item of the day. Keep the whole brief under 800 words. End with a "Sources" section listing the URLs you cited (just URLs, no commentary)."""

resp = client.messages.create(
    model="claude-opus-4-7",  # swap to claude-sonnet-4-5 if you want it cheaper
    max_tokens=4096,
    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 10}],
    system=SYSTEM,
    messages=[{
        "role": "user",
        "content": f"Today is {date_str}. Compile today's Leveraged Capital Markets morning brief. Search for the latest news from sources like Bloomberg, Reuters, WSJ, FT, S&P Global / LCD, PitchBook LCD, LevFin Insights, Debtwire, Reorg, and PE Hub."
    }],
)

# Pull all text blocks (the tool-use blocks get interleaved)
body = "\n".join(b.text for b in resp.content if b.type == "text")

# Convert to simple HTML
html = "<pre style='font-family: -apple-system, sans-serif; white-space: pre-wrap; font-size: 14px; line-height: 1.5;'>" + body + "</pre>"

resend.api_key = os.environ["RESEND_API_KEY"].strip()
resend.Emails.send({
    "from": "LevFin Brief <onboarding@resend.dev>",
    "to": [os.environ["TO_EMAIL"].strip()],
    "subject": f"LevFin Morning Brief — {today.strftime('%b %d')}",
    "html": html,
})

print("Sent.")