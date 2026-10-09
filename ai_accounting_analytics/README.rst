AI Accounting & Analytics
=========================

Ask your books in plain language - *"show the profit and loss for this month"*,
*"top 10 customers this year"*, *"which invoices are overdue?"* - and get the
answer streamed word by word, with live tables, charts and KPI cards computed by
Odoo through the Accounting Kit report engine.

Configuration
=============

1. Accounting > Configuration > AI Analytics > **My API Keys**: add your personal
   key (Google AI Studio, OpenAI, Anthropic or OpenRouter) and *Test Connection*.
2. Accounting > Configuration > Settings > **AI Analytics**: default model and
   token budget (max AI steps, history turns, max answer tokens, rows sent to the AI).
3. Accounting > **AI Analytics**: accept the one-time data sharing notice and ask.

Only Chief Accountants can use AI Analytics. Every AI call is logged under
*AI Usage & Cost* with its tokens and cost (USD).

How it works
============

The AI never sees raw tables and never writes SQL. It calls read-only tools
(``ai.accounting.toolkit``) that run with the user's access rights:

* Statements and overview: ``get_kpi_overview``, ``get_profit_and_loss``,
  ``get_balance_sheet``, ``get_trial_balance``, ``get_tax_summary``,
  ``get_cash_balances``.
* Partners and products: ``get_top_partners``, ``get_top_products``,
  ``get_aged_balance``, ``get_partner_summary``.
* Breakdowns and analysis: ``get_breakdown`` (sales, purchases, revenue,
  expenses or profit by partner, product, product category, account, journal,
  country, salesperson, analytic account or time, optionally split by a second
  dimension), ``get_trend``, ``compare_periods``, ``get_margins``,
  ``get_cash_forecast``, ``get_ratios`` (DSO, DPO, current/quick ratio, margins).
* Detail lookups: ``get_invoices``, ``get_invoice_details``, ``get_payments``,
  ``search_journal_items``, ``get_unreconciled_bank_lines``.
* Any other data: ``query_records`` (records or grouped totals of any business
  model, through the ORM with the user's access rights) and ``describe_data``
  (find models, list fields). Technical/security models (``ir.*``, users,
  groups, settings, mail, API keys, AI data) and secret-looking fields
  (password, token, secret, ...) are never reachable.

Questions that need no company data (accounting concepts, Odoo how-to, ...)
are answered from the model's own knowledge, without any tool call.

Each tool returns *display blocks* for the user (rendered by the browser and
exportable to the Accounting Kit PDF/XLSX reports) and a *compact payload* for
the AI.

Robustness
----------

AI models do not always follow the tool schemas: they send unused parameters
empty, numbers as text, values as synonyms ("customers", "monthly"), their own
parameter names (``start_date``) or periods in words ("October", "Q3 2026",
"last 7 days"). Every tool call goes through one normaliser
(``llm/arguments.py``) that turns such calls into exactly what the schema
declares, or returns a clear message naming the parameter and the accepted
values, so the AI fixes its call in one more step. Unknown parameters are
reported, never silently ignored, and a tool that fails unexpectedly is
logged and reported to the AI without ending the conversation.

Companies and deployment
------------------------

* Figures cover the companies selected in the company switcher (branches
  included when selected), for every tool alike. Companies in another
  currency than the current one are left out, and the AI is told so.
* Answers stream from a background thread; a ``ping`` line is sent every 10
  seconds of silence so proxies keep the connection open (nginx: keep
  ``proxy_buffering off`` or rely on the ``X-Accel-Buffering: no`` header).
* An answer is finished 15 seconds before the server's ``limit_time_real``
  (default 120 s, which kills longer requests in multi-worker mode): the AI
  stops calling tools in time to conclude. Raise ``limit_time_real`` (e.g. 300)
  for slow reasoning models.
* Stop, or closing the page, stops the answer at its next step; the answer
  is saved after every AI call, so what the user saw is kept.

Token saving
------------

* Tool calling instead of pasting data; tables and charts are never re-typed by the AI.
* Compact, rounded, row-limited tool results (``Rows Sent to the AI``).
* Periods (``this_month``, ``last_quarter``, ``this_year`` = fiscal year, ...) resolved
  server-side: no date reasoning by the model.
* Short system prompt and terse tool schemas, sorted for a byte-stable prefix that
  provider prompt caches can reuse (explicit ``cache_control`` for Claude).
* History sent as short digests (answer + one-line data summary), not raw tool data.
* Bounded agent loop (``Max AI Steps``); the last step must answer.
* Low reasoning effort / thinking budget preset per model (``Extra Request Parameters``).
* Chat titles from the question itself; connection tests list models (0 tokens).

Extending
=========

Add a tool from another module::

    class AiAccountingToolkit(models.AbstractModel):
        _inherit = 'ai.accounting.toolkit'

        def _ai_tool_specs(self):
            specs = super()._ai_tool_specs()
            specs['get_budget_status'] = {
                'description': 'Budget vs actual per budget line.',
                'parameters': {'period': P_PERIOD},
                'label': self.env._("Budgets"),
            }
            return specs

        def _ai_tool_get_budget_status(self, arguments):
            ...
            return {'model': {...}, 'blocks': [...], 'digest': '...'}

Tools receive normalised arguments (see Robustness). Add a baseline call for
the new tool to ``tests/test_tool_robustness.py``: the suite fails for any tool
without one, then fuzzes every parameter of it.

Tests
=====

``tests/`` runs without network access (the AI is scripted):

* ``test_tool_robustness``: every tool, every parameter, ~4,000 malformed or
  unusual values plus every enum value; output contract, read-only guard,
  empty company, limited users, contained failures.
* ``test_tool_semantics``: calls written as models write them return exactly
  the same data as the documented call; query security cannot be bypassed.
* ``test_question_scenarios``: real questions end to end with checked figures.
* ``test_agent_robustness`` / ``test_adapter_robustness``: odd tool names,
  repeated or flooding calls, empty, truncated or cut answers, every provider
  error, irregular provider streams.

Credits
=======

* Developer: Cybrosys Techno Solutions, https://www.cybrosys.com

License
=======

GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
