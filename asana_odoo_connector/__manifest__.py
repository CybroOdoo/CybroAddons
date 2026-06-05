# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

{
    'name': 'Asana Odoo Connector',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': "With this module, you can easily connect the projects, tasks "
               "and partners in the odoo to asana",
    'description': """With this module, user can connect the projects, tasks and
    the customers in the odoo to asana, which means the projects, tasks and 
    customers in the odoo can be seen in the asana also vice versa""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['project'],
    'data': [
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/project_task_type_views.xml',
        'views/res_config_settings_views.xml',
        'data/ir_actions_data.xml',
    ],
    'external_dependencies': {
        'python': [
            'asana',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
