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
    'name': "Sync Google Task With Project Task",
    'version': '20.0.1.0.0',
    'category': 'Services/Project',
    'summary': 'Export project tasks to Google Tasks and import Google tasks into your projects.',
    'description': """
     Sync your project tasks with Google Tasks. Connect your Google account
     once, then export tasks and their subtasks to your default Google Tasks
     list from the task form, the task list or an import/export wizard. The
     exported tasks are updated in Google Tasks when their name, description,
     deadline or subtasks change, and the tasks created in Google Tasks can
     be imported as Odoo tasks.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['project'],
    'data': [
        'security/ir.access.csv',
        'data/project_credential_data.xml',
        'views/project_credential_views.xml',
        'views/project_task_views.xml',
        'wizard/project_google_task_import_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
