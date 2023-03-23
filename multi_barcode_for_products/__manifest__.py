# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################

{
    'name': 'Product Multi Barcode For Sales,Purchase,Inventory and Invoicing',
    'version': '15.0.1.0.0',
    'summary': """Allows to create multiple barcode for a single product""",
    'description': """Allows to create Product multi barcode for Sales, Purchase, Inventory and Invoicing""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com/',
    'license': 'AGPL-3',
    'depends': ['stock', 'sale_management', 'purchase', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/product_product.xml',
        'views/product_template.xml',
        'views/product_template_search.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
