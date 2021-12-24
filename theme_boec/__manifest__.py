# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Theme Boec',
    'description': 'Theme Boec is an attractive and modern eCommerce Website theme',
    'summary': 'Theme Boec is a new kind of Theme. '
               'The theme is a very user-friendly and is suitable for your eCommerce website with blog.',
    'category': 'Theme/eCommerce',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_blog', 'website_sale_wishlist', 'website_sale',
                'website_sale_comparison'],
    'data': [
        'data/boec_config.xml',
        'data/boec_config_data.xml',
        'data/brand_filter.xml',
        'data/brand_inherit.xml',
        'data/hot_deals_button.xml',
        'security/ir.model.access.csv',
        'views/about.xml',
        'views/blog.xml',
        'views/blog_preview.xml',
        'views/cart.xml',
        'views/contact_us.xml',
        'views/footer.xml',
        'views/header.xml',
        'views/layouts.xml',
        'views/pages_top.xml',
        'views/product_view.xml',
        'views/shop.xml',
        'views/sidebar_shop.xml',
        'views/snippets/banner.xml',
        'views/snippets/blog_latest.xml',
        'views/snippets/deal_week.xml',
        'views/snippets/demo_product.xml',
        'views/snippets/insta_feed.xml',
        'views/snippets/product_tab.xml',
        'views/snippets/product_tab_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            ('replace', 'website_sale/static/src/js/website_sale_utils.js',
             'theme_boec/static/src/js/sale_utils.js'),
            "/theme_boec/static/src/css/style.css",
            "/theme_boec/static/src/css/style.css.map",
            "/theme_boec/static/src/css/style.scss",
            "/theme_boec/static/src/css/owl_carousel_min.css",
            "/theme_boec/static/src/css/owl_theme_default_min.css",
            "/theme_boec/static/src/js/owl.carousel.js",
            "/theme_boec/static/src/js/owl.carousel.min.js",
            "/theme_boec/static/src/js/jquery.countdown.min.js",
            "/theme_boec/static/src/js/deal_week.js",
            "/theme_boec/static/src/js/price_filter.js",
            "/theme_boec/static/src/js/product_tab.js",
            "/theme_boec/static/src/js/custom.js",
            "https://fonts.googleapis.com/css2?family=Karla:ital,wght@0,200;0,300;0,400;0,500;0,600;0,700;0,800;1,300;1,500&amp;family=Montserrat&amp;display=swap"

        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
