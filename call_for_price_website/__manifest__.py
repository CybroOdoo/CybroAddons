# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
    'version': '14.0.1.0.0',
    'category': 'Website',
    'summary': """Helps to hide price of specified product from shop""",
    'description': "The module aims to help website owners conceal the prices "
                   "of certain products from their online store. Instead of "
                   "displaying the price and an Add to Cart button, the module "
                   "replaces it with a customizable call-for-price message or "
                   "button. Customers interested in these products can use the "
                   "form that appears upon clicking the button to request more "
                   "information about the price, and they will receive a call "
                   "back from the store to discuss the pricing details",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale_wishlist', 'website_sale_comparison'],
    'data': ['security/ir.model.access.csv',
             'views/shop_hide_call_price_templates.xml',
             'views/shop_grid_templates.xml',
             'views/wishlist_hide_price_templates.xml',
             'views/hide_price_templates.xml',
             'views/compare_templates.xml',
             'views/call_for_price_views.xml',
             'views/product_template_views.xml',
             'views/assets.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
