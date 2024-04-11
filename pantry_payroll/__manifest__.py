# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
    'name': 'Payroll Management In Pantry',
    'version': '17.0.1.0.0',
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
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

