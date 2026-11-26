# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Partner Ledger with Partner Filter',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': """Print partner ledgers from contacts with partner and balance filters""",
    'description': """This module allows you to print partner ledgers from contacts with partner and balance filters.
     It provides a convenient way to generate partner ledger reports based on specific criteria,
      making it easier to analyze financial data related to your business partners.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'support': 'odoo@cybrosys.com',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'account', 'base_accounting_kit'],
    'data': ['report/report_partner_ledger.xml',
             'views/res_partner_views.xml',
             'wizard/account_report_general_ledger_views.xml'],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
