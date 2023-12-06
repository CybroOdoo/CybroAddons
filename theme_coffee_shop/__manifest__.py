# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM(odoo@cybrosys.com)
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
    'name': 'Theme Coffee Shop',
    'version': '15.0.1.0.0',
    'category': 'Theme/Creative',
    'summary': 'Theme Coffee Shop for Odoo Website e-Commerce',
    'description': 'Theme Coffee Shop, A more appealing and practical theme '
                   'for an e-Commerce Odoo website',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale_wishlist', 'auth_oauth'],
    'data': [
        'data/menus_data.xml',
        'views/header.xml',
        'views/footer.xml',
        'views/contact_us.xml',
        'views/cart.xml',
        'views/cart_lines.xml',
        'views/cart_popover.xml',
        'views/cart_summary.xml',
        'views/payment_summary.xml',
        'views/shop.xml',
        'views/about_us.xml',
        'views/feature.xml',
        'views/menu_page.xml',
        'views/product.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_coffee_shop/static/src/css/style.css',
            'theme_coffee_shop/static/src/js/action.js',
        ],
    },
    'images': ['static/description/banner.png',
               'static/description/theme_screenshot.jpeg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
