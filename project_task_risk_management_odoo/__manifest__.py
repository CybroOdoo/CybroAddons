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
        'security/project_task_risk_management_odoo_groups.xml',
        'security/ir.model.access.csv',
        'views/project_risk_incident_line_views.xml',
        'views/task_risk_incident_line_views.xml',
        'views/menu_actions.xml',
        'views/menuitems.xml',
        'views/project_project_views.xml',
        'views/risks_project_views.xml',
        'views/risk_type_views.xml',
        'views/risk_category_views.xml',
        'views/risk_response_views.xml',
        'views/risk_tag_views.xml',
        'views/risk_incident_views.xml',
        'views/project_task_views.xml',
        'wizard/risk_incident_simplified_views.xml',
    ],
    'post_init_hook': '_post_init_hook',
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
