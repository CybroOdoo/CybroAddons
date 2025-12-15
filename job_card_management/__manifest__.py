# -*- coding: utf-8 -*-
###################################################################################
#    Job Card Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Manasa T P (<https://www.cybrosys.com>)
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
###################################################################################
{
    'name': 'Job Card Management',
    'version': '16.0.1.0.0',
    'category': 'Job Card Management',
    'summary': 'Job Card Management',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'description': "Job Card Management",
    'depends': ['hr', 'project', 'purchase', 'account', 'hr_timesheet'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/job_card_views.xml',
        'views/workshop_views.xml',
        'views/hr_employee_views.xml',
        'views/material_requisition_views.xml',
        'views/job_card_menu_views.xml',
        'data/job_card_data.xml',
        'report/job_card_report.xml',
        'report/cost_sheet.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
