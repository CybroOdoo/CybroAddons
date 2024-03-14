# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'version': '17.0.1.0.0',
    'category': 'Theme',
    'summary': 'A Captivating and Practical E-Commerce Theme for Coffee Shops',
    'description': 'Theme Coffee Shop brings a captivating and highly '
                   'practical theme crafted exclusively for e-Commerce'
                   ' websites specializing in coffee shops. With its blend of '
                   'aesthetic appeal and user-centric design, this theme '
                   'provides an exceptional browsing and shopping experience '
                   'for coffee enthusiasts and customers.It encapsulates the'
                   ' essence of a cozy coffee shop, translating it into an '
                   'engaging online platform for your coffee products and '
                   'accessories.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale_wishlist', 'auth_oauth', 'website_sale', 'sale'],
    'data': [
        'data/website_menu_data.xml',
        'views/header.xml',
        'views/footer.xml',
        'views/contact_us.xml',
        'views/cart_lines.xml',
        'views/shop.xml',
        'views/about_us.xml',
        'views/feature.xml',
        'views/menu_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_coffee_shop/static/src/css/style.css',
        ],
    },
    'images': ['static/description/banner.jpg',
               'static/description/theme_screenshot.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
