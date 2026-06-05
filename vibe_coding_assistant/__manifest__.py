# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
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
################################################################################
{
    "name": "Odoo Vibe Coding Assistant",
    "version": "19.0.1.0.0",
    "summary": "Chat with AI to generate downloadable Odoo modules",
    "description": """
Odoo Vibe Coding Assistant
==========================
A Discuss-style chat interface that turns natural-language requests into
fully generated, downloadable Odoo 19 modules. Supports Gemini (default),
Claude, and OpenAI via per-user API keys.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "license": "LGPL-3",
    "category": "Productivity",
    "depends": ["base", "web"],
    "data": [
        "security/vibe_groups.xml",
        "security/ir.model.access.csv",
        "security/vibe_security.xml",
        "data/ai_provider_data.xml",
        "data/vibe_prompt_templates_data.xml",
        "views/ai_provider_views.xml",
        "views/ai_provider_user_config_views.xml",
        "views/vibe_prompt_template_views.xml",
        "views/vibe_dashboard_views.xml",
        "views/vibe_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vibe_coding_assistant/static/src/**/*.js",
            "vibe_coding_assistant/static/src/**/*.xml",
            "vibe_coding_assistant/static/src/**/*.scss",
        ],
    },
    "application": True,
    'images': ['static/description/banner.jpg'],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "_refresh_provider_models_hook",
    "post_load": None,
}
