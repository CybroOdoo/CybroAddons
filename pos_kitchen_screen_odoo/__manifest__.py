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
    'name': 'POS Kitchen Screen',
    'version': '20.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': 'POS Kitchen Screen facilitates sending certain orders '
               'automatically to the kitchen. The POS Kitchen Screen allows for '
               'the customization of order views, so that staff can see the '
               'information that is most important to them.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'pos_restaurant', 'bus'],
    'data': [
        'security/pos_kitchen_screen_groups.xml',
        'security/ir.access.csv',
        'data/kitchen_screen_data.xml',
        'views/kitchen_screen_views.xml',
        'views/pos_kitchen_screen_odoo_menus.xml',
        'views/pos_order_views.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_kitchen_screen_odoo/static/src/js/order_pay.js',
            'pos_kitchen_screen_odoo/static/src/js/order_button.js',
        ],
        'web.assets_backend': [
            'pos_kitchen_screen_odoo/static/src/css/kitchen_screen.css',
            'pos_kitchen_screen_odoo/static/src/js/kitchen_screen.js',
            'pos_kitchen_screen_odoo/static/src/xml/kitchen_screen_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
