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
    'name': 'Field Time Picker',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Time Picker Widget for Character Fields',
    'description': 'Field Time Picker enhances the time input functionality in '
                   'Odoo',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web'],
    "assets": {
        'web.assets_backend': [
            'field_timepicker/static/src/xml/timepicker_templates.xml',
            'field_timepicker/static/src/css/time_widget.css',
            'field_timepicker/static/src/js/time_widget.js',
        ],
        'web.assets_unit_tests': [
            'field_timepicker/static/tests/**/*.test.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
