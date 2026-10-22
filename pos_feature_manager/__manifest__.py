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
    'name': 'POS Feature Manager',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Restrict POS features per user/employee (Payments, Discount, Qty, Price, etc.)',
    'description': """
        This module allows administrators to restrict or enable specific POS features
        for individual users or employees. Control access to:
        - Payments
        - Discounts
        - Quantity changes
        - Price editing
        - Remove order lines
        - Customer selection
        - +/- Button
        - Numpad
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'hr', 'pos_hr'],
    'data': [
        'views/res_users_views.xml',
        'views/hr_employee_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_feature_manager/static/src/js/pos_restrictions.js',
        ],
    },
    'images': [
        'static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
