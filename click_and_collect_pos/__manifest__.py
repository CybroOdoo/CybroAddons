# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
    'name': 'Click And Collect PoS',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'With this module, customers may place product orders online '
               'and pick them up from the closest shop.',
    'description': 'This module enables customers to order products online '
                   'and pick them up from the closest shop. ',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'point_of_sale', 'sale_management', 'stock'],
    'data': [
        'views/click_and_collect_button.xml',
        'views/pos_config_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'click_and_collect_pos/static/src/js/website_sale_cart.js',
        ],
        'point_of_sale.assets': [
            'click_and_collect_pos/static/src/js/sale_order_button.js',
            'click_and_collect_pos/static/src/js/click_and_collect_screen.js',
            'click_and_collect_pos/static/src/scss/sale_order.scss',
        ],
        'web.assets_qweb': [
            'click_and_collect_pos/static/src/xml/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
