# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P(<https://www.cybrosys.com>)
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
    'name': 'Payroll Management In Pantry',
    'version': '15.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Efficiently oversee payroll operations by factoring in 
     pantry expenditures through seamless deductions""",
    'description': """This app will allow us to Manage Payroll of Pantry.
     While creating Employee Payslip ,Salary Rule will be Added to that 
     Employee. The Amount of Product will Deduct from Salary.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'depends': ['sale', 'hr_payroll_community'],
    'data': [
        'security/pantry_payroll_security.xml',
        'security/ir.model.access.csv',
        'data/salary_rule_data.xml',
        'data/ir_sequence_data.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/pantry_order_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
