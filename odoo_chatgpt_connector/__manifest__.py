# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu(odoo@cybrosys.com)
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
################################################################################


{
    'name': 'Odoo ChatGPT Connector',
    'version': '16.0.1.0.1',
    'summary': 'Odoo ChatGPT Language Connector',
    'description': 'Allows the application to leverage the capabilities of the GPT language model to generate human-like responses, providing a more natural and intuitive user experience',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': ['base', 'website'],
    'data': [
        'views/chatgpt_menu.xml',
        'views/chatgpt_setting_views.xml',
        'views/chatgpt_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_chatgpt_connector/static/src/js/submit_request.js',
            'odoo_chatgpt_connector/static/src/css/container.css'
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
