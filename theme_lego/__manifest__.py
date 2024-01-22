# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fouzan M (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Theme Lego',
    'version': '17.0.1.0.0',
    'category': 'Theme',
    'summary': 'Design Web Pages with Theme Lego',
    'description': 'Theme Lego is an ideal choice for your Odoo 17.'
                   'This theme promises to offer a refreshing experience with Odoo,'
                   'enhancing its functionality and aesthetics."',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale_wishlist',
                'website_sale_comparison'],
    'data': [
        'views/footer_templates.xml',
        'views/shop_templates.xml',
        'views/add_to_cart_templates.xml',
        'views/payment_templates.xml',
        'views/login_templates.xml',
        'views/header_templates.xml',
        'views/address_templates.xml',
        'views/deal_back_views.xml',
        'views/snippets/snippet_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            "/theme_lego/static/src/css/owl.carousel.min.css",
            "/theme_lego/static/src/css/owl.theme.default.min.css",
            "/theme_lego/static/src/css/style.css",
            "/theme_lego/static/src/js/owl.carousel.js",
            "/theme_lego/static/src/js/owl.carousel.min.js",
            "/theme_lego/static/src/js/index.js",
            "/theme_lego/static/src/js/deal.js",
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
