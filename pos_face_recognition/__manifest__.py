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
    'name': 'Pos Face Recognition',
    'version': '20.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'User can log in to POS session using face recognition method',
    'description': 'User can log in to a POS session using face recognition '
                   'method. If an unauthorized login is detected, a warning '
                   'message is raised.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['pos_hr'],
    'data': [
        'views/hr_employee_views.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_face_recognition/static/lib/face-api/face-api.min.js',
            'pos_face_recognition/static/src/css/pos_face_recognition.css',
            'pos_face_recognition/static/src/js/selection_popup.js',
            'pos_face_recognition/static/src/xml/selection_popup.xml',
        ],
        'web.assets_unit_tests': [
            'pos_face_recognition/static/tests/unit/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
