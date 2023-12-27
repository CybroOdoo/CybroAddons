# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    'name': 'Theme Boec',
    'version': '17.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': "Theme Boec is an attractive and modern eCommerce Website "
               "theme",
    'description': "Theme Boec is new kind of Theme.The theme is very user-friendly"
                   "and suitable for your eCommerce website with blog",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_blog', 'website_sale_wishlist', 'website_sale',
                'website_sale_comparison'],
    'data': [
        'security/ir.model.access.csv',
        'data/boec_config_data.xml',
        'views/about.xml',
        'views/blog_templates.xml',
        'views/blog_preview_templates.xml',
        'views/cart_templates.xml',
        'views/contact_us_templates.xml',
        'views/footer_templates.xml',
        'views/header_templates.xml',
        'views/layout_templates.xml',
        'views/page_top_templates.xml',
        'views/product_view_templates.xml',
        'views/shop_templates.xml',
        'views/boec_config_views.xml',
        'views/product_brand_views.xml',
        'views/product_template_views.xml',
        'views/sidebar_shop_templates.xml',
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
            'theme_boec/static/src/js/sale_utils.js',
            "/theme_boec/static/src/css/style.css",
            "/theme_boec/static/src/css/style.css.map",
            "/theme_boec/static/src/css/style.scss",
            "/theme_boec/static/src/css/owl_carousel_min.css",
            "/theme_boec/static/src/css/owl_theme_default_min.css",
            "/theme_boec/static/src/js/owl.carousel.js",
            "/theme_boec/static/src/js/owl.carousel.min.js",
            "/theme_boec/static/src/js/jquery.countdown.min.js",
            "/theme_boec/static/src/js/deal_week.js",
            "/theme_boec/static/src/js/product_tab.js",
            "/theme_boec/static/src/js/custom.js",
            "https://fonts.googleapis.com/css2?family=Karla:ital,wght@0,200;0,300;0,400;0,500;0,600;0,700;0,800;1,300;1,500&amp;family=Montserrat&amp;display=swap"
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
