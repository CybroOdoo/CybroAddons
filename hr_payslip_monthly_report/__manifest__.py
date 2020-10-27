# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Anusha (<https://www.cybrosys.com>)
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
    'name': 'Payroll Advanced Features',
    'summary': 'Payroll Advanced Features For Odoo 13 Community.',
    'description': 'Payroll Advanced Features For Odoo 13 Community, payroll, odoo13, payroll report, payslip report',
    'category': 'Generic Modules/Human Resources',
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'hr_payroll_community', 'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip.xml',
        'views/res_config_settings_views.xml',
        'data/payslip_mail_template.xml',
        'wizard/hr_payslip_mass_confirm.xml',
        'report/hr_payslip_report.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

