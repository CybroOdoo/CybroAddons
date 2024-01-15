# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
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
    'name': 'Whatsapp Live Chat In Odoo',
    'version': '15.0.1.0.0',
    'summary': """The Whatsapp Live Chat In Odoo app is designed to facilitate
     real-time communication between businesses and their customers using the 
     popular messaging platform,WhatsApp.""",
    'description': """This module is designed to facilitate real-time 
     communication between businesses and their customers using the popular 
     messaging platform,WhatsApp.With Whatsapp Live Chat In Odoo, businesses can
     offer immediate support, answer inquiries, and provide personalized 
     assistance to customers through the familiar WhatsApp interface.""",
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base', 'contacts', 'stock', 'website', 'website_sale'
    ],
    'data': [
        'views/res_config_settings_views.xml',
        'views/integration_whatsapp_chat_live_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'integration_whatsapp_chat_live/static/src/css/wp_msg.css',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
