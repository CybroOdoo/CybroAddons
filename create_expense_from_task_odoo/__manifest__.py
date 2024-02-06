# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
{
    'name': "Create Expense From Task",
    'version': "17.0.1.0.0",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'description': "This apps helps User to create multiple expense "
                   "from project task and split the amount between assigns",
    'summary': 'User can create Expense from Task',
    'category': 'Services/Project',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'hr_expense', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_expense_views.xml',
        'views/project_task_views.xml',
        'wizards/expense_amount_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
