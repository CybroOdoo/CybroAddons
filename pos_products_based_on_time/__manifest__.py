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
    'name': 'POS Happy Hours | POS Time Based Products | POS Breakfast Lunch Dinner',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Show different products in the POS at different times of
     the day, such as breakfast, lunch, dinner or happy hours""",
    'description': """With the help of this module, you can show different
    products in the POS at different times of the day. The products for each
    time range are chosen by the user in the Product Planning menu.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'mail'],
    'data': [
        'security/ir.access.csv',
        'security/security_rule.xml',
        'views/meals_planning_menu.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_products_based_on_time/static/src/js/meals_planning_model.js',
            'pos_products_based_on_time/static/src/js/pos_planning.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
