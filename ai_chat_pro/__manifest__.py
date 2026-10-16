# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Odoo AI Chat Pro',
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'live_test_url': 'https://www.youtube.com/embed/oZj-6IlYyRQ?autoplay=1&mute=1&loop=1&playlist=oZj-6IlYyRQ&controls=1&rel=0&modestbranding=1',
    'summary': 'Ask questions about your business data in plain language, at a minimal AI cost',
    'description': """
Odoo AI Chat Pro
===========

An AI assistant that answers questions on your Odoo data, such as
"list me the top 10 sale orders", "which purchases cost me the most" or
"invoices due today":

* An agent, not a pipeline: each message is first understood by Odoo's AI service
  (OLG) in one small call (what it asks, the request written as a whole, the
  data, names, count and chart it gives), then the right tool answers it: data,
  record creation, duplication, explanation, report, import or deep analysis
* The decision model (Jev) plans each query and decides, with its confidence, whether
  the data is enough, a short explanation is needed, or a deep analysis is worth it
* The data models a question is about are detected automatically from the menus
  and models the user can access: no model is hard coded
* The AI only writes a small query plan: records are read by Odoo itself, as the
  current user, so access rights, record rules and companies always apply
* Every question is decided anew, never answered from a cache, and the prompts are kept very small, to
  cost few tokens
* Questions that need an analysis are answered by Odoo's AI service (OLG)
* Questions can be asked by voice: the recording is turned into text by a speech to text model of
  OpenRouter, chosen in the settings, and its cost is shown apart
* Answers with data download as professional PDF reports, printed by the report engine of Odoo,
  with an executive summary written by Odoo's AI service
* A chat screen, a chat window in the systray, and settings for the OpenRouter key and model
    """,
    'depends': ['web', 'iap', 'mail', 'base_import'],
    'data': [
        'security/ai_chat_pro_security.xml',
        'security/ir.access.csv',
        'data/ai_chat_pro_data.xml',
        'views/ai_chat_conversation_views.xml',
        'views/res_config_settings_views.xml',
        'views/ai_chat_pro_menus.xml',
        'report/ai_chat_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ai_chat_pro/static/src/**/*.scss',
            'ai_chat_pro/static/src/**/*.js',
            'ai_chat_pro/static/src/**/*.xml',
        ],
    },
    'images': ['static/description/banner.gif'],
    'auto_install': False,
    'application': True,
    'installable': True,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'license': 'LGPL-3',
}
