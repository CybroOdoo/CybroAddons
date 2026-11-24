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
    'name': 'Import Employee Task Checklist in Project',
    'version': '20.0.1.0.0',
    'category': 'Project',
    'summary': 'Import task checklist via Excel and CSV',
    'description': """Import task checklist records from CSV and Excel files (.xls, .xlsx)
    into Project Task Checklists in Odoo 20.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['project', 'projects_task_checklists'],
    'external_dependencies': {
        'python': ['xlrd', 'openpyxl'],
    },
    'data': [
        'security/ir.access.csv',
        'views/task_checklist_views.xml',
        'wizards/import_checklist_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'import_task_checklist/static/src/css/import_task_checklist.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
