# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Pos Order Line Items Count',
    'version': '15.0.1.0.0',
    'summary': 'Module to show the count, quantity of items in the pos screen'
               ' and pos receipt',
    'description': 'This module helps to show the count, quantity of items in'
                   ' the pos screen and pos receipt',
    'category': 'Point of Sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'point_of_sale.assets': [
            'pos_orderline_items_count/static/src/js/pos_receipt.js',
            'pos_orderline_items_count/static/src/js/product_screen.js',
        ],
        'web.assets_qweb': [
            'pos_orderline_items_count/static/src/xml/pos_items_count.xml',
            'pos_orderline_items_count/static/src/xml/pos_receipt.xml',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
