# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Automatic Project Task Timer',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Automatic Running Timer for Project Tasks',
    'description': "This module helps you to track time sheet in project "
                   "using a real timer, it's starts when task is in "
                   "configured stage and stops when its moves to any other "
                   "stage and the timesheet will be recorded.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_views.xml',
        'views/res_config_settings_views.xml',
        'views/timer_configuration_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'automatic_project_task_timer/static/src/js/task_timer.js',
            'automatic_project_task_timer/static/src/js/form_open.js',
            'automatic_project_task_timer/static/src/xml/task_timer_templates.xml',
        ]},
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
