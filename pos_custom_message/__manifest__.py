# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
    'name': 'POS Custom Message',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Custom popup messages in pos screen',
    'description': "This Module allows you to create custom messages that "
                   "will be displayed at a specific time on the Point of Sale "
                   "(POS) screen. These messages can be used to remind users "
                   "of important tasks, warn them about potential problems, "
                   "or provide them with other information.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_custom_message_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_custom_message/static/src/js/*.js',
            'pos_custom_message/static/src/xml/pos_popup_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'licence': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
