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
    'name': 'Automatic Project Task Timer',
    'version': '20.0.1.0.0',
    'category': 'Project',
    'summary': 'Automatic Running Timer for Project Tasks',
    'description': "This module helps you track timesheets in projects "
                   "using an automatic timer. It starts when a task enters "
                   "the configured stage and stops when it moves to any "
                   "other stage, automatically recording the timesheet.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr_timesheet'],
    'data': [
        'security/ir.access.csv',
        'views/project_task_views.xml',
        'views/res_config_settings_views.xml',
        'views/timer_configuration_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'automatic_project_task_timer/static/src/js/task_timer.js',
            'automatic_project_task_timer/static/src/js/form_open.js',
            'automatic_project_task_timer/static/src/xml/task_timer_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
