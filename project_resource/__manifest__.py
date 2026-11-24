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
    'name': "Project Free Resource",
    'version': '20.0.1.0.0',
    'category': 'Project',
    'summary': """Get all free resources for the project""",
    'description': """This module helps retrieve all available resources for a
    project task based on the task start and end dates, allowing assignment
    to one of them.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    'depends': ['project'],
    'data': [
        'security/ir.access.csv',
        'views/project_task_views.xml',
        'views/res_users_view.xml',
        'wizards/free_resource_view.xml'
    ],
    "images": ["static/description/banner.jpg"],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
