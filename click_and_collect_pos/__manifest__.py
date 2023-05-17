# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
    'name': 'Click And Collect PoS',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'With this module, customers may place product orders online '
               'and pick them up from the closest shop.',
    'description': 'This module enables customers to order products online '
                   'and pick them up from the closest shop. ',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'images': ['static/description/banner.png'],
    'depends': [
        'base', 'website_sale', 'point_of_sale', 'sale_management', 'stock'],
    'data': [
        'views/click_and_collect_button.xml',
        'views/pos_config.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'click_and_collect_pos/static/src/js/website_sale_cart.js',
        ],
        'point_of_sale.assets': [
            'click_and_collect_pos/static/src/xml/sale_order_button.xml',
            'click_and_collect_pos/static/src/js/sale_order_button.js',
            'click_and_collect_pos/static/src/xml/chrome.xml',
            'click_and_collect_pos/static/src/js/click_and_collect_screen.js',
            'click_and_collect_pos/static/src/xml/click_and_collect_screen.xml',
            'click_and_collect_pos/static/src/scss/sale_order.scss',
            'click_and_collect_pos/static/src/js/pos_model_load.js'
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
