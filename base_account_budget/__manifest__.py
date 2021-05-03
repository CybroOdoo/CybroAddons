# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Odoo 14 Budget Management',
    'version': '14.0.1.0.1',
    'summary': """ Budget Management for Odoo 14 Community Edition. """,
    'description': """ This module allows accountants to manage analytic and budgets.

     Once the Budgets are defined (in Accounting/Accounting/Budgets), the Project Managers
     can set the planned amount on each Analytic Account.
     
     The accountant has the possibility to see the total of amount planned for each
     Budget in order to ensure the total planned is not greater/lower than what he
     planned for this Budget. Each list of record can also be switched to a graphical
     view of it.
     
     Three reports are available:

     1. The first is available from a list of Budgets. It gives the spreading, for
     these Budgets, of the Analytic Accounts.
     2. The second is a summary of the previous one, it only gives the spreading,
     for the selected Budgets, of the Analytic Accounts.
     3. The last one is available from the Analytic Chart of Accounts. It gives
     the spreading, for the selected Analytic Accounts of Budgets. 
     Odoo 14 Budget Management,Odoo 14, Odoo 14 Budget, Odoo 14 Accounting, 
     Odoo 14 Account,Budget Management, Budget""",
    'category': 'Accounting',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'account'],
    'website': 'https://www.cybrosys.com',
    'data': [
        'security/ir.model.access.csv',
        'security/account_budget_security.xml',
        'views/account_analytic_account_views.xml',
        'views/account_budget_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
