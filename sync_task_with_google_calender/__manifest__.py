# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
{
    'name': 'Google Calendar Integration For Project And Task',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Module For Integrating Odoo Project With Google Calender.',
    "description": """Google Calendar Integration for Project Tasks odoo app 
    helps users to sync project tasks with google Calendar. Users can get all
    task information like name, description, create date time, deadline, and 
    attende, If a user updates a task then google calendar events also get 
    updated.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'project', 'google_calendar'],
    'data': [
        'views/res_users_views.xml',
        'views/project_task_views.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
