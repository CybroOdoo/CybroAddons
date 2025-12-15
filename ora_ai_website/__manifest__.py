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
    'name': 'Ora-Ai Website',
    'version': '18.0.1.0.0',
    'category': 'eCommerce',
    'summary': """Ora-AI Website enables users to place product orders using
    the voice assistant directly through the website.""",
    'description': """Ora Website Assistant,By implementing this module
    voice-activated technology, your customers can easily browse your eCommerce
    store, inquire about products, and place orders, all by speaking naturally
    to the AI.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'ora_ai_base', 'website_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/templates.xml',
        'views/website_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ora_ai_website/static/src/js/website_templates.js',
            'ora_ai_website/static/src/scss/website_template.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'auto_install': False,
    'installable': True,
    'application': False
}
