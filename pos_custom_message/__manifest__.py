# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

{
    'name': 'POS Custom Message',
    'version': '18.0.1.0.0',
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
        'point_of_sale._assets_pos': [
            'pos_custom_message/static/src/app/screens/product_screen.js',
            'pos_custom_message/static/src/app/utils/alert_popup/alert_popup.js',
            'pos_custom_message/static/src/app/utils/alert_popup/alert_popup.xml',
            'pos_custom_message/static/src/app/utils/info_popup/info_popup.js',
            'pos_custom_message/static/src/app/utils/info_popup/info_popup.xml',
            'pos_custom_message/static/src/app/utils/warning_popup/warning_popup.js',
            'pos_custom_message/static/src/app/utils/warning_popup/warning_popup.xml'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
