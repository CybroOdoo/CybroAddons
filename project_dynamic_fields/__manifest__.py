# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (<https://www.cybrosys.com>)
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
    'name': 'Project Dynamic Fields',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': "Adding Custom Fields for Project Module",
    'description': """Adding Custom Fields for Project Module,Odoo16.
                  Easy to track  how many custom fields are created .
                  There is no need of technical knowledge to create custom fields""",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base', 'project'
    ],
    'data':
        [
            'security/project_dynamic_fields_groups.xml',
            'security/ir.model.access.csv',
            'data/project_dynamic_fields_widget_data.xml',
            'views/ir_model_fields_views.xml',
            'wizard/project_dynamic_fields_views.xml',
        ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
