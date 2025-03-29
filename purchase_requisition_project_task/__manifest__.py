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
    'name': 'Purchase Requisition & Project Task Integration',
    'version': '17.0.1.0.0',
    'category': 'Project,Purchase',
    'summary': """Purchase Requisition and Project Task module relate project,
                  task and purchase requisition""",
    'description': "Purchase Requisition and Project task module helps to "
                   "select the project and task from purchase agreements. "
                   "And the selected project and task will show the created "
                   "agreement in their form view.Also this module helps to "
                   "group the purchase requisitions based on the selected "
                   "project and task.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['project', 'purchase_requisition'],
    'data': [
             'views/purchase_requisition_views.xml',
             'views/project_project_views.xml',
             'views/project_task_views.xml'
            ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
