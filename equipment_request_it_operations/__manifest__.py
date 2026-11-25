# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arshad Ali Pottengal (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Equipment Request & IT Operation",
    'version': "19.0.1.0.0",
    'category': 'Human Resources',
    'summary': "Employees request equipment and damage reimbursements, "
               "approved by the department manager and HR.",
    'description': """This module allows employees to send equipment requests
    and equipment damage expense reimbursement requests to the Department
    Manager of Equipment. The workflow requires approval from the Department
    Manager, followed by approval from the HR Officer for both equipment
    requests and damage reimbursement requests.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr_expense', 'stock'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/equipment_request_views.xml',
        'report/equipment_report.xml',
        'report/equipment_report_template.xml',
        'views/menu_action.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
