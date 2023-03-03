# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayisha Sumayya K(odoo@cybrosys.com)
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
    'name': 'Coffee Shop',
    'description': 'Theme Coffee Shop',
    'summary': 'Theme Coffee Shop',
    'version': '16.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Theme/Creative',
    'depends': ['website_sale', 'website_sale_wishlist','auth_oauth', ],
    'data': [
        'data/menu.xml',
        'views/header.xml',
        'views/login.xml',
        'views/footer.xml',
        'views/contact_us.xml',
        'views/cart.xml',
        'views/cart_lines.xml',
        'views/cart_popover.xml',
        'views/cart_summary.xml',
        'views/payment.xml',
        'views/payment_summary.xml',
        'views/product.xml',
        'views/address.xml',
        'views/shop.xml',
        'views/about_us.xml',
        'views/feature.xml',
        'views/menu_page.xml',
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
    'auto_install': False,
    'installable': True,
    'application': False
}

