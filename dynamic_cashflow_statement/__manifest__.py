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
    'name': 'Dynamic Cash Flow Statements',
    'version': '18.0.1.0.0',
    'summary': """Generates a Dynamic Statement that Highlights Cash Inflows 
                and Outflows.""",
    'description': """Provides a drill-down view of cashflow statements, 
                    allowing users to easily navigate and analyze 
                    journal entries.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Accounting',
    'depends': ['base', 'account', 'account_payment'],
    'data': [
             'security/ir.model.access.csv',
             'views/cashflow_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            "dynamic_cashflow_statement/static/src/js/cashflow.js",
            "dynamic_cashflow_statement/static/src/xml/cashflow.xml",
            "dynamic_cashflow_statement/static/src/css/cashflow.css",
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
