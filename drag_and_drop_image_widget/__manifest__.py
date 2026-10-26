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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Drag and Drop Image Widget',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Widget for drag-and-drop images into the image field',
    'description': "This module is used to drag and drop images into the image field",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'drag_and_drop_image_widget/static/src/scss/drag_and_drop.scss',
            'drag_and_drop_image_widget/static/src/js/drag_and_drop.js',
            'drag_and_drop_image_widget/static/src/xml/drag_and_drop_templates.xml',
        ],
        'web.assets_unit_tests': [
            'drag_and_drop_image_widget/static/tests/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
