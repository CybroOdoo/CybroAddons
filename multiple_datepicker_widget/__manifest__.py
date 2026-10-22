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
    'name': 'Multiple DatePicker Widget',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Widget for picking multiple dates in Odoo 20',
    'description': 'Allows users to select and store multiple dates in a field '
                   'using an interactive calendar date picker',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': [
            'multiple_datepicker_widget/static/src/lib/flatpickr/flatpickr.min.css',
            'multiple_datepicker_widget/static/src/lib/flatpickr/flatpickr.min.js',
            'multiple_datepicker_widget/static/src/css/datepicker_widget.css',
            'multiple_datepicker_widget/static/src/js/multiple_date_picker_widget.js',
            'multiple_datepicker_widget/static/src/xml/datepicker_widget_templates.xml',
        ],
        'web.assets_unit_tests': [
            'multiple_datepicker_widget/static/tests/**/*.test.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
