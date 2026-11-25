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
#############################################################################
{
    'name': "Ora-AI Base",
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Ora-AI base module helps to configure the voice assistant.',
    'description': 'Ora-AI base module provides core configurations and '
                   'services necessary to integrate and manage a voice '
                   'assistant within the Odoo environment.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'mail', 'account'],
    'data': [
        'security/voice_assistant_security.xml',
        'security/ir.access.csv',
        'data/client_action.xml',
        'data/provider_model_data.xml',
        'data/transcriber_model_data.xml',
        'data/ora_language_data.xml',
        'views/ora_ai_views.xml',
        'views/ora_file_view.xml',
        'views/ora_call_history_views.xml',
        'views/ora_language_views.xml',
        'views/res_config_settings_views.xml',
        'views/vapi_menus.xml',
        'views/standard_model_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'assets': {
        'web.assets_backend': [
            'ora_ai_base/static/src/lib/vapi.min.js',
            'ora_ai_base/static/src/js/ora_voice_data.js',
            'ora_ai_base/static/src/js/ora_ai.js',
            'ora_ai_base/static/src/js/systray_voice_assistant.js',
            'ora_ai_base/static/src/xml/ora_ai_base_templates.xml',
            'ora_ai_base/static/src/xml/ora_ai_base_voice_data_templates.xml',
            'ora_ai_base/static/src/xml/systray_voice_assistant.xml',
            'ora_ai_base/static/src/scss/ora_ai.scss',
        ],
    },
    'external_dependencies': {"python": ["googletrans"]},
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
