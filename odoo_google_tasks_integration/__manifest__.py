# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
{
    'name': "Sync Google Task With Project Task",
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Module For Integrating Google Tasks.',
    'description': """Google Task Integration for Project Tasks odoo app 
     helps users to sync project tasks with google task.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['project', 'google_calendar', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/project_credential_data.xml',
        'views/project_credential_views.xml',
        'views/project_task_views.xml',
        'wizard/project_google_task_import_views.xml',
    ],
    'images': [
        'static/description/banner.jpg'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
