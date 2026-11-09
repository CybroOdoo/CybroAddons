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
    'name': 'Project Report XLS & PDF',
    'version': '20.0.1.0.0',
    'category': 'Project',
    'summary': 'Print project tasks as a PDF report or an XLSX spreadsheet, '
               'filtered by stage and assignee.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['project', 'web'],
    'external_dependencies': {'python': ['xlsxwriter']},
    'data': [
        'security/ir.access.csv',
        'report/project_report_reports.xml',
        'report/project_report_template.xml',
        'wizard/project_report_views.xml',
        'views/project_project_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'project_report_pdf/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
