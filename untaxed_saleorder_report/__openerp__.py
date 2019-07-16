# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Tax Dissolved Sale Order Report',
    'version': '0.2',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'category': 'Sales Management',
    'summary': """ Module gives the Tax Dissolved (In Total Amount) SO/Customer Invoice Print""",
    'description': """ Module gives the Tax Dissolved (In Total Amount) SO/Customer Invoice Print""",
    'depends': ['sale', 'account'],
    'images': ['static/description/banner.jpg'],
    "data": [
        "views/without_tax_report_account_view.xml",
        "views/without_tax_account_view.xml",
        "views/without_tax_sale_view.xml",
        "views/without_tax_report_sale_view.xml",
    ],
    'installable': True,
    'auto_install': False,
}


