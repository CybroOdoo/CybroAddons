# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'version': '16.0.1.0.0',
    'summary': 'Project Task Risk Management Odoo',
    'description': """Project Task Risk Management Odoo""",
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
    ],
    'data': [
        'security/user_groups.xml',
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
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
