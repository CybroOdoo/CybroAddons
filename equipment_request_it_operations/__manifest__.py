# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    'name': "Equipment Request & IT Operations",
    'version': "16.0.1.0.0",
    'category': 'Human Resources',
    'description': "This module allows your employees to send requests to "
                   "the Department Manager of Equipment for"
                   "equipment type as equipment requests and equipment "
                   "damage expense reimbursement requests Followed"
                   "by Department manager approval and HR Officer approval "
                   "workflow for equipment request and"
                   "equipment damage request",
    'summary': 'Create Equipment Requests',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'hr_expense', 'hr', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/user_groups.xml',
        'views/equipment_request_views.xml',
        'report/equipment_report.xml',
        'report/equipment_report_template.xml',
        'views/menu_action.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
