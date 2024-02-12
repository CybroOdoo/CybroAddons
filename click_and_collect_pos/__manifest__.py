# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
    'name': 'Click And Collect PoS',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """With this module, customers may place product orders online
    and pick them up from the closest shop.""",
    'description': """This module facilitates customers to conveniently order 
    products online and opt for a click-and-collect service, enabling them to 
    pick up their purchases from the nearest store.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'images': ['static/description/banner.jpg'],
    'depends': [
        'base', 'website_sale', 'point_of_sale', 'sale_management', 'stock'],
    'data': [
        'views/cart_line_template.xml',
        'views/pos_config_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml'
    ],
    'assets': {
        'web.assets_frontend': [
                'click_and_collect_pos/static/src/js/website_sale_cart.js',
              ],
        'point_of_sale._assets_pos': [
            'click_and_collect_pos/static/src/js/navbar.js',
            'click_and_collect_pos/static/src/xml/navbar.xml',
            'click_and_collect_pos/static/src/js/click_and_collect_screen.js',
            'click_and_collect_pos/static/src/scss/sale_order.scss',
            'click_and_collect_pos/static/src/xml/click_and_collect_screen.xml',
            'click_and_collect_pos/static/src/js/pos_store.js',
            'click_and_collect_pos/static/src/xml/chrome.xml',
            ]
     },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
