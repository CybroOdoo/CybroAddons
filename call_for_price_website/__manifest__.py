# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
    'version': '16.0.2.0.0',
    'category': 'Website',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'website_sale', 'website_sale_wishlist',
                'website_sale_comparison', 'stock'],
    'summary': """Helps to hide price of specified product from shop""",
    'description': "Hide price and add to cart item button of All page stores"
                   "and user must ask for a call for price",
    'data': ['security/ir.model.access.csv',
             'views/shop_hide_call_price_template.xml',
             'views/wishlist_hide_price_template.xml',
             'views/compare_hide_price_template.xml',
             'views/call_for_price_views.xml',
             'views/product_product_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/call_for_price_website/static/src/js/create_call_form.js',
            '/call_for_price_website/static/src/js/variant_mixin.js'
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
