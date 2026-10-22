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
    'name': 'Image Capture Widget',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Allows users to capture and upload images directly from the webcam.""",
    'description': """This module is used to add Image Capture Widget for Image 
     Field. We can capture the image from the webcam and upload into the binary
     field.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'image_capture_upload_widget/static/src/scss/image_capture.scss',
            'image_capture_upload_widget/static/src/js/image_capture.js',
            'image_capture_upload_widget/static/src/xml/image_capture_templates.xml',
        ],
        'web.assets_unit_tests': [
            'image_capture_upload_widget/static/tests/**/*',
            ('remove', 'image_capture_upload_widget/static/tests/tours/**/*'),
        ],
        'web.assets_tests': [
            'image_capture_upload_widget/static/tests/tours/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
