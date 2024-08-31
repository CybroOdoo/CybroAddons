# -*- coding: utf-8 -*-
###################################################################################
#    POS Order Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Akhil(<https://www.cybrosys.com>)
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
###############################################################################
{
    'name': 'POS Order Management',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "POS All Order's Management",
    'description': """Module allows you to display all the old orders in Point of Sale.
    You will get the detailed view of Order Reference, Receipt Reference, Customer and Order Date.""",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/res_config_settings_views.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_all_orders/static/src/js/models.js',
            'pos_all_orders/static/src/js/all_order_button.js',
            'pos_all_orders/static/src/xml/all_order_button.xml',
            'pos_all_orders/static/src/xml/all_order_screen.xml',
            'pos_all_orders/static/src/js/all_order_screen.js',
            'pos_all_orders/static/src/xml/partner_screen.xml',
            'pos_all_orders/static/src/js/partner_screen.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
