## Module <ai_accounting_analytics>

#### 01.10.2026
#### Version 20.0.1.0.0
#### ADD
- Initial release: AI Analytics chat for Odoo 20 Community (Gemini, OpenAI, Claude, OpenRouter),
  read-only accounting tools on top of the Accounting Kit, per-user API keys, one-time consent,
  token and cost tracking.

#### 09.10.2026
#### Version 20.0.1.0.0
#### UPDT
- Tool arguments normalised for every provider: empty optional values, numbers and booleans as
  text, enum synonyms, parameter aliases, periods in words ("October", "Q3 2026", "last 7 days")
  and flexible dates; dates sent without period=custom are applied, unknown parameters reported.
- Generic queries: domain values checked against field types, Python-style and single-condition
  domains, operator aliases, aggregates written as sum(field); no traversal into technical models,
  "any!" refused.
- Agent: prefixed tool names, repeated calls answered from the first one, at most 8 calls per
  step, empty answers retried, truncated answers flagged, cut streams retried, unexpected tool
  failures contained.
- Robustness test suites (fuzzing of every tool parameter, equivalence of call styles, question
  scenarios, provider stream irregularities).
- Company scope: every tool covers the companies selected in the switcher (branches included),
  the same as generic queries; companies in another currency are left out and reported.
- Answers stream from a background thread with keep-alive pings, stop when the page is closed
  or Stop is pressed, are saved after every AI call and finish before limit_time_real.
