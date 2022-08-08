# -*- coding: utf-8 -*-
###################################################################################

#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Swapna V (<https://www.cybrosys.com>)
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
    'name': "Products/Variants Purchase Price History",
    'summary': """Purchase price history report of products/variants """,
    'description': """Purchase price history report of products/variants""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'maintainer': "Cybrosys Techno Solutions",
    'category': 'Purchase',
    'version': '15.0.1.0.0',
    'depends': [
        'base',
        'product',
        'purchase',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_line_wiz.xml',
        'reports/report.xml',
        'reports/pdf_report_template.xml',
        'views/product_product_inherit.xml',
        'views/product_template_inherit.xml',
        'views/purchase_order_inherit.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}
