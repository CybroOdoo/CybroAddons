# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme Lego',
    'version': '15.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Design Web Pages with Theme Lego',
    'description': ' Theme Lego Is A Ultimate Theme for Your Odoo 15.'
               'This Theme Will Give You A New Experience With Odoo',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png'
    ],
    'depends': ['web', 'website_sale_wishlist',
                'website_sale_comparison'],
    'data': [
        'views/footer_templates.xml',
        'views/shop_templates.xml',
        'views/website_cart_templates.xml',
        'views/payment_templates.xml',
        'views/login_templates.xml',
        'views/checkout_templates.xml',
        'views/header_templates.xml',
        'views/product_template_views.xml',
        'views/snippets/snippet_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            "/theme_lego/static/src/css/owl.carousel.min.cs",
            "/theme_lego/static/src/css/owl.theme.default.min.css",
            "/theme_lego/static/src/css/style.css",
            "/theme_lego/static/src/js/owl.carousel.min.js",
            "/theme_lego/static/src/js/index.js",
            "/theme_lego/static/src/js/deal.js",
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
