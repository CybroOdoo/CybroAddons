# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
    'name': 'Product Expiry Dashboard',
    'version': '15.0.1.0.0',
    'category': 'Warehouse',
    'summary': """Allow users to view all the product details those are going to 
     expire.""",
    'description': """Product Expiry Dashboard display graphical view of 
     expiredproducts, nearly expiring products, their locations and 
     warehouses. This app allows take significant decisions quickly by 
     overseeing the products that will expire soon""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock', 'product_expiry'],
    'data': ['views/product_expiry_view.xml'],
    'assets': {
        'web.assets_backend': [
            '/odoo_product_expiry_dashboard/static/src/js/product_expiry_action.js',
            '/odoo_product_expiry_dashboard/static/src/css/style.css',
            'https://cdn.jsdelivr.net/npm/chart.js'
        ],
        'web.assets_qweb': [
            '/odoo_product_expiry_dashboard/static/src/xml/odoo_product_expiry_dashboard.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
