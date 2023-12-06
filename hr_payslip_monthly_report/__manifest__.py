# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen  (odoo@cybrosys.com)
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
#############################################################################
{
    'name': 'Payroll Advanced Features',
    'version': '16.0.1.0.0',
    'category':  'Human Resource',
    'summary': 'Payroll Advanced Features For Odoo 16 Community includes'
               ' Payslip monthly reports and Mass Confirm Payslip',
    'description': 'Payroll Advanced Features For Odoo 16 Community includes '
                   'Payroll-Payslip Reporting, Automatic Mail During '
                   'Confirmation of Payslip, Mass Confirm Payslip ',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'depends': [
        'hr_payroll_community', 'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_views.xml',
        'views/res_config_settings_views.xml',
        'data/payslip_mail_template.xml',
        'wizard/payslip_confirm_views.xml',
        'report/hr_payroll_report_view_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
