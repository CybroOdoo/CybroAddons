# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
{
    'name': 'Laundry Management',
    'version': '20.0.1.0.0',
    "category": "Industries",
    'summary': """Complete Laundry Service Management""",
    'description': 'This module helps manage all processes in a laundry service.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale','product', 'account', ],
    'data': [
        'security/laundry_management_security.xml',
        'security/ir.access.csv',
        'data/laundry_management_data.xml',
        'data/ir_sequence_data.xml',
        'views/laundry_order_views.xml',
        'views/washing_washing_views.xml',
        'views/washing_type_views.xml',
        'views/report_laundry_order_views.xml',
        'views/washing_work_views.xml',
        'views/label_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
