{
    'name': 'Odoo MCP Server',
    'version': '18.0.1.0.0',
    'category': 'Productivity/AI',
    'license': 'LGPL-3',
    'summary': 'Odoo MCP Server, MCP Server, Odoo AI Server',
    'description': """
AI Connector Hub
================
Odoo MCP Server, Claude Odoo Connector, AI Odoo Connector

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
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_mcp_manager/static/src/js/ai_json_editor.js',
            'odoo_mcp_manager/static/src/xml/ai_json_editor.xml',
        ],
    },
    'external_dependencies': {
        'python': ['pydantic', 'mcp', 'jinja2', 'requests'],
    },
    'installable': True,
    'images': ['static/description/banner.jpg'],
    'application': True,

}
