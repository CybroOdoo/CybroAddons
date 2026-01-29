# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Project and Task Progress Status',
    'version': '15.0.1.0.0',
    'category': 'Project',
    'summary': 'Keep your finger on the projects pulse with this module. '
               'Featuring a dynamic progress bar, it provides a visual snapshot'
               'of project and task advancement. Toggle effortlessly between'
               'Kanban and list views for a personalized project tracking '
               'experience.',
    'description': 'Dive into project progression with a sleek module offering'
                   ' a task-focused progress bar. Switch between Kanban and '
                   'list views seamlessly, ensuring a comprehensive '
                   'understanding of your projects evolving landscape. '
                   'Streamline your workflow and meet deadlines with ease.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr_timesheet', 'project'],
    'data': [
        'views/project_task_types_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
