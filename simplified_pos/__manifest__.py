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
    'name': 'Simplified POS',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Manage all POS operations on a single page.',
    'description': 'A straightforward point-of-sale system that enables '
                   'payment, order confirmation, and product selection all on '
                   'the same page.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.access.csv',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'simplified_pos/static/src/**/*',
        ],
        'web.assets_unit_tests_setup': [
            'simplified_pos/static/src/js/**/*',
            'simplified_pos/static/src/xml/**/*',
        ],
        'web.assets_unit_tests': [
            'simplified_pos/static/tests/unit/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
