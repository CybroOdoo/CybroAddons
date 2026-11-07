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
    'name': "PSQL Query Execute",
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Execute PostgreSQL queries directly in Odoo UI and export results to Excel (XLSX).""",
    'description': """The PSQL Query Execute module allows administrators and developers to run PostgreSQL queries directly within the Odoo user interface and export tabular results into Excel (XLSX) format.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail'],
    'data': [
        'security/ir.access.csv',
        'views/psql_query_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'psql_query_execute/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'application': False,
    'auto_install': False,
}
