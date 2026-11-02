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
    'name': 'Inventory Turnover Analysis Report',
    'version': '20.0.1.0.0',
    'category': "Warehouse",
    'summary': """Generate inventory turnover analysis reports in PDF, XLSX, list and graph views.""",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['stock', 'sale', 'purchase'],
    'external_dependencies': {'python': ['xlsxwriter']},
    'data': [
        'security/ir.access.csv',
        'views/fetch_data_views.xml',
        'views/turnover_graph_analysis_views.xml',
        'report/turnover_report_templates.xml',
        'wizard/turnover_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_turnover_report_analysis/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
