# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Asana Odoo Connector',
    'version': '15.0.1.0.0',
    'category': 'Project',
    'summary': "This module enables seamless integration between Odoo and Asana,"
               "allowing synchronization of projects, tasks, and partners",
    'description': """This module facilitates the connection between Odoo and 
                    Asana, ensuring that projects, tasks, and customers in Odoo 
                    are synchronized with Asana. Any updates made in Odoo 
                    reflect in Asana and vice versa, enabling efficient project 
                    management and collaboration across both platforms. With 
                    this integration, businesses can streamline their workflows,
                     track progress effortlessly, and enhance team productivity
                      by managing tasks in their preferred environment.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['project'],
    'data': [
        'data/ir_actions_server_data.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/project_task_type_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'external_dependencies': {
        'python': [
            'asana',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
