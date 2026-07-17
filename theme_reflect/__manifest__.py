# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Theme Reflect',
    'version': '17.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'A clean, minimal fashion-forward Odoo website theme inspired by modern editorial aesthetics.',
    'description': """Theme Reflect is a modern Odoo 17 eCommerce theme designed for fashion and lifestyle websites 
with a clean and elegant user interface. It includes customizable homepage snippets, enhanced shop and product pages,
responsive layouts, and interactive features to provide a seamless online shopping experience.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale_wishlist', 'website_blog'],
    'data': [
        'views/snippets/s_hero_banner.xml',
        'views/snippets/s_category_grid.xml',
        'views/snippets/s_product_highlight.xml',
        'views/snippets/s_editorial.xml',
        'views/snippets/s_features.xml',
        'views/snippets/s_newsletter.xml',
        'views/snippets/s_brand_marquee.xml',
        'views/snippets/s_new_arrivals.xml',
        'views/snippets/s_cta_banner.xml',
        'views/snippets/s_testimonials.xml',
        'views/snippets/snippets.xml',
        'views/layout.xml',
        'views/pages/homepage.xml',
        'views/pages/about.xml',
        'views/shop.xml',
        'views/product.xml',
        'views/checkout.xml',
    ],
    'assets': {
        'web._assets_frontend_helpers': [
            'theme_reflect/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_reflect/static/src/scss/theme.scss',
            'theme_reflect/static/src/scss/layout.scss',
            'theme_reflect/static/src/scss/components.scss',
            'theme_reflect/static/src/scss/snippets.scss',
            'theme_reflect/static/src/scss/ecommerce.scss',
            'theme_reflect/static/src/js/theme.js',
            'theme_reflect/static/src/js/snippets.animation.js',
            'theme_reflect/static/src/js/cart_sidebar.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
