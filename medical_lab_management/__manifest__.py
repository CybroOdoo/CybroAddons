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
    'name': "Medical Lab Management",
    'version': '20.0.1.0.0',
    'category': 'Industries',
    'summary': """Manage Medical Lab Operations.""",
    'description': 'A longer description of what this module does.',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/medical_lab_management_security.xml',
        'security/ir.access.csv',
        'data/lab_appointment_sequence.xml',
        'data/lab_patient_sequence.xml',
        'data/lab_request_sequence.xml',
        'views/res_partner_views.xml',
        'views/lab_patient_views.xml',
        'views/test_unit_views.xml',
        'views/lab_test_views.xml',
        'views/lab_test_content_type_views.xml',
        'views/physician_specialty_views.xml',
        'views/physician_details_views.xml',
        'views/lab_request_views.xml',
        'views/lab_appointment_views.xml',
        'views/account_move_views.xml',
        'report/lab_request_reports.xml',
        'report/lab_patient_reports.xml',
        'report/lab_request_templates.xml',
        'report/lab_patient_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
