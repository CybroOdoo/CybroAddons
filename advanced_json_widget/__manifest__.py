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
    'name': 'Advanced JSON Widget',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Interactive JSON Field Editor Widget for Odoo""",
    'description': """
        This module provides a user-friendly widget for editing JSON data fields in Odoo, 
        allowing easy management of key-value pairs through an intuitive interface without
        the need for manual JSON syntax formatting.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            "advanced_json_widget/static/src/**/*"
        ],
        'web.assets_unit_tests': [
            "advanced_json_widget/static/tests/**/*",
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
