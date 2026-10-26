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
    'name': 'POS Numpad Show/Hide',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Toggle numpad visibility in the Point of Sale screen',
    'description': """
POS Numpad Show/Hide
====================
This module allows cashiers to easily show or hide the numpad on the Point of Sale screen using a toggle button, optimizing screen space for product browsing and order management.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_numpad_show_hide/static/src/xml/pos.xml',
            'pos_numpad_show_hide/static/src/js/pos_numpad.js',
        ],
        'web.assets_tests': [
            'pos_numpad_show_hide/static/tests/tours/**/*',
        ],
        'web.assets_unit_tests': [
            'pos_numpad_show_hide/static/tests/unit/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
