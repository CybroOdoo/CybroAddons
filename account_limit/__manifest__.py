# -*- coding: utf-8 -*-
#
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Account Credit Limit',
    'version': '10.0.2.0',
    'summary': """Generate Warning Message When Credit Limit of an Account is Exceed.""",
    'description': """Account credit limit is a handy plugin for Odoo Accounting module to set a Credit limit
    for each Account. The module will bring new fields total Credit, Debit and Balance in ‘Accounts tree view’ and
    ‘Account form view’. The module also produce a warning message while making journal entries which will exceed
    the credit limit. The features can simplify the credit evaluation process of accounts like Customers accounts,
    Overdraft accounts, Bank accounts etc.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Accounting',
    'depends': ['account', 'account_accountant'],
    'license': 'LGPL-3',
    'data': ['views/account_credit_limit_view.xml'],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
