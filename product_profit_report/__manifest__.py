# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
#
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
###############################################################################
{
    'name': 'Product Profit Report',
    'version': '13.0.1.0.0',
    'category': 'Productivity',
    'summary': 'The product profit report module provides detailed insights '
               'and analysis on the profitability of individual products',
    'description': 'This module generates a report specifically focused on '
                   'analyzing the profitability of different products within '
                   'a business. This module provides valuable insights into '
                   'the financial performance of individual products, '
                   'allowing businesses to make informed decisions regarding '
                   'their product offerings, pricing strategies, and resource '
                   'allocation.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'sale_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'report/product_profit_report_templates.xml',
        'report/product_profit_report.xml',
        'wizard/product_profit_report_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
