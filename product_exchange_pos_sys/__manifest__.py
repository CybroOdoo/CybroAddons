# -*- coding: utf-8 -*-
###################################################################################
#    POS Product Exchange
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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
    'name': 'POS Product Exchange V16',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'POS Product Exchange',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'description': "POS Product Exchange",
    'depends': ['base', 'point_of_sale'],
    'images': ['static/description/banner.png'],
    'data': [
        'views/pos_order.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'product_exchange_pos_sys/static/src/js/models.js',
            'product_exchange_pos_sys/static/src/js/all_order_screen.js',
            'product_exchange_pos_sys/static/src/xml/all_order_screen.xml',
            'product_exchange_pos_sys/static/src/js/order_button.js',
            'product_exchange_pos_sys/static/src/xml/order_button.xml',
            'product_exchange_pos_sys/static/src/js/exchange_order.js',
            'product_exchange_pos_sys/static/src/xml/exchange_order.xml',
            'product_exchange_pos_sys/static/src/scss/pos.scss'
        ],

    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
