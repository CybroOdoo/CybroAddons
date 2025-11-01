# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': 'Generative AI In Snippet Creation',
    'version': '18.0.1.0.0',
    'category': 'Generative AI/Generative AI',
    'summary': 'To integrate AI tools in website snippet creation.',
    'description': """This module contains details about Generative AI in website.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base', 'website', 'web', 'web_editor'
    ],
    'external_dependencies': {
        'python': [
            'openai',
            ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/test_data.xml',
        'views/res_config_settings_views.xml',
        'views/snippets/s_snippet_group_with_ai_content.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web_editor.assets_wysiwyg': [
            'generative_ai/static/src/xml/website_dialogue_box.xml',
            'generative_ai/static/src/js/ai_button_action.js',
            ('include', 'web._assets_helpers'),
            'generative_ai/static/src/js/title.js',
        ],
        'web.assets_backend': [
            'generative_ai/static/src/img/placeholder.png',
            'generative_ai/static/src/css/snippets.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
