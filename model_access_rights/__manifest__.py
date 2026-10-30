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
    'name': 'Hide Create|Delete|Archive|Export Options - Model Wise',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools, Productivity',
    'summary': """Hide Create, Delete, Archive, and Export options per model""",
    'description': """This module allows administrators to hide Create, Delete,
    Export, and Archive/Unarchive options on specific models for designated
    users or user groups.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/model_access_rights_security.xml',
        'security/ir.access.csv',
        'views/access_right_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'model_access_rights/static/src/**/*',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
