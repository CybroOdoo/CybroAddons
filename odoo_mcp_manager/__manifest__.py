# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
##############################################################################
{
    'name': 'Odoo MCP Server',
    'version': '19.0.1.0.0',
    'category': 'Productivity/AI',
    'summary': 'Odoo MCP Server, MCP Server, Odoo AI Server',
    'description': """Odoo MCP Server, Claude Odoo Connector, AI Odoo Connector

Key Features:
- Unified Provider & Model Management
- Advanced Tool Framework (@ai_tool)
- Full MCP Server Implementation
- AI-Ready Messaging (mail.message extension)
- User Consent Injection for sensitive tools
- AI Hub Dashboard & Tool Logging
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/default_ai_providers.xml',
        'data/default_ai_tools.xml',
        'data/default_ai_resources.xml',
        'wizards/fetch_model_wizard_views.xml',
        'wizards/generate_mcp_key_views.xml',
        'wizards/test_tool_wizard_views.xml',
        'views/ai_provider_views.xml',
        'views/ai_model_views.xml',
        'views/ai_tool_views.xml',
        'views/ai_resource_views.xml',
        'views/ai_session_views.xml',
        'views/ai_tool_log_views.xml',
        'views/ai_consent_views.xml',
        'views/ai_bot_channel_views.xml',
        'views/res_config_settings_views.xml',
        'views/ai_hub_dashboard_views.xml',
        'views/menus.xml',
        'views/bot_conversation_views.xml',
        'wizards/fetch_model_wizard_views.xml',
        'wizards/generate_mcp_key_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'odoo_mcp_manager/static/src/css/mcp_dashboard.css',
            'odoo_mcp_manager/static/src/js/ai_json_editor.js',
            'odoo_mcp_manager/static/src/xml/ai_json_editor.xml',
            'odoo_mcp_manager/static/src/js/mcp_dashboard.js',
            'odoo_mcp_manager/static/src/xml/mcp_dashboard.xml',
        ],
    },
    'external_dependencies': {
        'python': ['pydantic', 'mcp', 'jinja2', 'requests'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,


    'auto_install': False,
}
