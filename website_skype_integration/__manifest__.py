# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Website Skype Integration',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'This module provides live chats through Skype on a website.',
    'description': 'This feature is handy for conducting live chats through '
                   'Skype on a website. Skype provides free online calling, '
                   'messaging services, cost-effective international calls to '
                   'mobiles or landlines, and Skype for Business for efficient '
                   'collaboration.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website'],
    'data': ['views/website_templates.xml',
             'views/res_config_settings_views.xml'],
    'assets': {
        'web.assets_frontend': [
            'website_skype_integration/static/src/css/skype_chat_button.css',
        ],
    },
    'images': [
        'static/description/banner.jpg'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
