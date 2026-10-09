# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'AI Accounting & AI Analytics for Community: Chat with your Books (Gemini, ChatGPT, Claude, OpenRouter)',
    'version': '20.0.1.0.0',
    'category': 'Accounting',
    'summary': """Ask your accounting in plain language: profit and loss, balance sheet,
    aged balances, top customers, cash, taxes, trends - answered with live
    tables and charts. Odoo 20 AI accounting, AI analytics, ChatGPT, Gemini,
    Claude, OpenRouter, accounting assistant for community.""",
    'description': """
AI Accounting & Analytics
=========================
An AI analyst inside Odoo Accounting. Users ask questions in natural language
("show the profit and loss for this month", "top 10 customers this year")
and the assistant answers with figures computed by Odoo itself - through the
Accounting Kit report engine - rendered as streaming text, tables and charts.

* Providers: Google Gemini, OpenAI (ChatGPT), Anthropic (Claude), OpenRouter.
* Per-user API keys, one-time data-sharing consent.
* Read-only tool calling: the model never sees raw tables or writes SQL.
* Token and cost tracking per call, per user and per model.
* Token-saving design: compact tool results, server-side period resolution,
  short history digests, prompt caching and bounded agent steps.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base_accounting_kit', 'mail'],
    'data': [
        'security/ir.access.csv',
        'data/ai_accounting_provider_data.xml',
        'views/ai_accounting_provider_views.xml',
        'views/ai_accounting_model_views.xml',
        'views/ai_accounting_api_key_views.xml',
        'views/ai_accounting_usage_views.xml',
        'views/ai_accounting_chat_views.xml',
        'views/res_config_settings_views.xml',
        'views/ai_accounting_analytics_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ai_accounting_analytics/static/src/variables.scss',
            'ai_accounting_analytics/static/src/chat/**/*',
            'ai_accounting_analytics/static/src/usage/**/*',
        ],
        'web.assets_tests': [
            'ai_accounting_analytics/static/tests/tours/**/*',
        ],
    },
    'external_dependencies': {
        'python': ['requests'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
