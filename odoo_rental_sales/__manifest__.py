# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswathi PN (odoo@cybrosys.com)
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
    'name': 'Odoo Rental Sales',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': "The module helps in rental management.",
    'description': "This module allows businesses to create rental orders, "
                   "track the availability of rental products, and manage rental "
                   "contracts and invoices.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com',
    'depends': ['product', 'sale_management', 'base'],
    'data': [
        'security/rental_order_contract_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_corn_data.xml',
        'wizard/rental_product_views.xml',
        'views/product_views.xml',
        'views/odoo_rental_sales_menus.xml',
        'views/sale_order_views.xml',
        'views/rental_order_contract_views.xml',
        'views/rental_product_category_views.xml',
        'views/rental_product_agreement_views.xml',
        'views/uom_views.xml'
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
