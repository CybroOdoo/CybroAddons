# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Total Items and Total Quantity in POS',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "To Show the Total Quantity and Total Items Ordered in POS",
    'description': "This app will shows the number of "
                   "products ordered and the total quantity"
                   " of products in the order summary in"
                   " the pos screen and bill.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'pos_self_order'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'total_quantity_pos/static/src/overrides/components/order_receipt.js',
            'total_quantity_pos/static/src/overrides/components/order_receipt.xml',
            'total_quantity_pos/static/src/overrides/components/order_widget.js',
            'total_quantity_pos/static/src/overrides/components/order_widget.js',
            'total_quantity_pos/static/src/overrides/components/order_widget.xml',

        ],

    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
