# Topic profile: Markets research (passive)

This is a **research** topic, not a trading instruction. The output is
a daily markdown brief over public, primary sources. Nothing in this
profile produces orders, signals, or executable trades.

## Topic string (paste into TOPIC env var or workflow_dispatch input)

```
Daily macro and markets briefing: central-bank announcements, regulatory
filings (SEC EDGAR, ESMA, FCA), exchange rule changes, listed-company
8-Ks/10-Qs, ETF flows reported by issuers, IPO prospectuses (S-1/F-1),
publicly-disclosed crypto protocol changelogs, and macroeconomic data
releases (BLS, BEA, ECB, BoJ). Surface only what was first published in
the last 24 hours.
```

## Source-type allowlist

Hard-restrict to primary sources:

- Regulatory filings: SEC EDGAR, ESMA register, FCA, FINMA, MAS.
- Central bank releases: Federal Reserve, ECB, BoE, BoJ, PBoC, RBI.
- Exchange notices: NYSE, Nasdaq, CBOE, ICE, LSE, JPX, HKEX, CME.
- Statistical agencies: BLS, BEA, Eurostat, ONS, StatCan.
- First-party crypto changelogs: Ethereum core repo, Bitcoin core repo,
  Solana repo, official protocol blog posts.
- Issuer press releases hosted on the issuer's own domain or a regulated
  newswire when republished verbatim.

## Disallowed

- Trading signals, "alpha calls", whale-watching channels, telegram
  pump groups.
- Aggregator commentary unless used only as a citation pointer to a
  primary source.
- Any prompt that asks the agent to recommend a buy/sell/hold action.
  The brief reports what happened; it does not advise.

## Output additions on top of base RunOutput

- For every event with a number (rate, CPI, EPS, AUM): include the
  released figure, the prior figure, and the consensus number if the
  primary source reports one. If consensus is only available from a
  secondary, omit it and add a gap row.
- Tag each source with `jurisdiction` in the notes field where
  applicable (US, EU, UK, JP, etc.).

## Run

```bash
TOPIC="$(cat claude_research_stack/topics/markets_research.md | sed -n '/^```$/,/^```$/p' | sed '1d;$d' | head -1)" \
  python -m claude_research_stack.src.run_daily
```

Or via Actions: trigger **Research Daily Loop** → set the `topic` input
to the topic string above.
