# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
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
##############################################################################
{
    'name': 'Odoo Jira Connector',
    'version': '17.0.1.0.0',
    'category': 'Project',
    'summary': 'Odoo Jira Connector is a valuable integration tool for '
               'businesses that use both Odoo and Jira. By connecting these '
               'two systems, businesses can streamline their project '
               'management processes and improve their overall efficiency.',
    'description': 'The Odoo Jira Connector offers a range of features, '
                   'including bi-directional synchronization of data, '
                   'automatic creation of Jira issues from Odoo records, and '
                   'real-time updates of Jira issues in Odoo. To meet the '
                   'specific needs of any business users can leverage, they '
                   'can use Odoo to handle their business.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
        'views/project_views.xml',
        'views/project_task_type_views.xml',
        'views/jira_sprint_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
    'pre_init_hook': 'pre_init_hook'
}
