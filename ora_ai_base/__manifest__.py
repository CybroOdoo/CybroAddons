# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Ora-Ai Base",
    'version': '18.0.1.0.0',
    'category': 'eCommerce',
    'summary': 'Ora-Ai base module helps to configure the voice assistant.',
    'description': 'Ora-AI base module provides core configurations and '
                   'services necessary to integrate and manage a voice '
                   'assistant within the Odoo environment.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'bus', 'mail', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/client_action.xml',
        'data/provider_model_data.xml',
        'data/transcriber_model_data.xml',
        'data/ora_langauage_data.xml',
        'views/ora_ai_views.xml',
        'views/ora_file_view.xml',
        'wizard/res_config_settings_views.xml',
        'views/vapi_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ora_ai_base/static/src/js/ora_voice_data.js',
            'ora_ai_base/static/src/js/ora_ai.js',
            'ora_ai_base/static/src/xml/ora_ai_base_templates.xml',
            'ora_ai_base/static/src/xml/ora_ai_base_voice_data_templates.xml',
            'ora_ai_base/static/src/scss/ora_ai.scss',
            'ora_ai_base/static/src/scss/style.scss',
            'https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.3.8/dist/vapi.min.js'
        ],
    },
    'external_dependencies': {"python": ["zeep"]},
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'auto_install': False,
    'installable': True,
    'application': True,
}
