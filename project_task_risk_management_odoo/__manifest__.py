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
    'name': 'Project Task Risk Management Odoo',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Risk Management For Project & Tasks',
    'description': """This module allows project manager and users to 
    manage risk on the project and tasks with risk incident creation from 
    project and tasks.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['project'],
    'data': [
        'security/project_task_risk_management_odoo.xml',
        'security/ir.model.access.csv',
        'wizard/risk_incident_wiz.xml',
        'views/project_risk_analysis.xml',
        'views/task_risk_analysis.xml',
        'views/menu_actions.xml',
        'views/menuitems.xml',
        'views/project_project.xml',
        'views/risks_project.xml',
        'views/risk_type.xml',
        'views/risk_category.xml',
        'views/risk_response.xml',
        'views/risk_tags.xml',
        'views/risk_incident.xml',
        'views/project_task.xml',
    ],
    'post_init_hook': '_post_init_hook',
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
