# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nikhil M (odoo@cybrosys.com)
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
    'name': 'Website Call For Price',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': """Helps to hide price of product from shop""",
    'description': "Hide price and add to cart item button of All page stores"
                   "and user must ask for a call for price",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'website_sale_stock', 'website_sale_wishlist',
                'website_sale_comparison'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_templates.xml',
        'views/call_for_price_views.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/call_for_price_website/static/src/js/variant.js'
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
