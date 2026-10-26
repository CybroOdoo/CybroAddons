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
    'name': 'Employee Stages',
    'version': '20.0.1.0.0',
    'category': "Human Resources",
    'summary': """Manages Employee Lifecycle Stages and Career History""",
    'description': """Every employee may undergo different stages during their
    tenure in a company. It may be probation, training, employment, notice
    period, etc. The stages may vary according to the organization. It is
    important to track such stages systematically to assess employee career
    progression. This module facilitates the management and tracking of different
    stages throughout an employee's career lifecycle.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr'],
    'data': [
        'security/ir.access.csv',
        'wizard/employee_stage_views.xml',
        'views/hr_employee_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
