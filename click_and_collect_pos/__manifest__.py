# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################

{
    'name': 'Click And Collect POS',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Order products online and pick them up at the closest POS store.',
    'description': """This module facilitates customers to conveniently order
    products online and opt for a click-and-collect service, enabling them to
    pick up their purchases from the nearest store.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'point_of_sale', 'sale_stock', 'pos_sale'],
    'data': [
        'views/cart_line_template_views.xml',
        'views/pos_config_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'click_and_collect_pos/static/src/js/website_sale_cart.js',
            'click_and_collect_pos/static/src/css/cart.css',
        ],
        'point_of_sale._assets_pos': [
            'click_and_collect_pos/static/src/js/navbar.js',
            'click_and_collect_pos/static/src/xml/navbar.xml',
            'click_and_collect_pos/static/src/js/click_and_collect_screen.js',
            'click_and_collect_pos/static/src/xml/click_and_collect_screen.xml',
            'click_and_collect_pos/static/src/css/style.css',
        ],
        'web.assets_unit_tests_setup': [
            'click_and_collect_pos/static/src/js/**/*',
            'click_and_collect_pos/static/src/xml/**/*',
        ],
        'web.assets_unit_tests': [
            'click_and_collect_pos/static/tests/unit/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
