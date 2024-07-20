# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (<https://www.cybrosys.com>)
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
    'name': 'Theme Diva',
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': """Design Web Pages with Theme Diva. The theme is very '
    'user-friendly and is suitable for your website.""",
    'description': """Theme Diva is an attractive and modern eCommerce 
     Website theme""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'website_blog', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_featured_data.xml',
        'views/featured_configuration.xml',
        'views/views.xml',
        'views/customize.xml',
        'views/layout.xml',
        'views/myaccount.xml',
        'views/shop.xml',
        'views/product_view.xml',
        'views/contact.xml',
        'views/index_layout/index_banner.xml',
        'views/index_layout/index_main_product.xml',
        'views/index_layout/index_featured_product.xml',
        'views/index_layout/index_demo.xml',
        'views/index_layout/index_subscribe.xml',
        'views/home_index/banner.xml',
        'views/home_index/popular_product.xml',
        'views/home_index/Featured_product.xml',
        'views/home_index/testimonial.xml',
        'views/home_index/offer.xml',
        'views/home_index/index2_blog.xml',
        'views/diva_index/index3_banner.xml',
        'views/diva_index/index3_product.xml',
        'views/diva_index/index3_store.xml',
        'views/diva_index/index3_gallery.xml',
        'views/diva_index/index3_blog.xml',
        'views/landing_page/landing_features.xml',
        'views/landing_page/landing_demo.xml',
        'views/landing_page/landing_banner.xml',
        'views/landing_page/landing_sponsored.xml',
        'views/landing_page/landing_subscribe.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.30.1/moment.min.js',
            '/theme_diva/static/src/xml/home_index_blog.xml',
            '/theme_diva/static/src/xml/index_layout_blog.xml',
            '/theme_diva/static/src/xml/index_featured_products.xml',
            '/theme_diva/static/src/xml/index_featured_products2.xml',
            '/theme_diva/static/src/xml/index_main_product.xml',
            '/theme_diva/static/src/css/style.css',
            'theme_diva/static/src/css/pluginstyle.css',
            '/theme_diva/static/src/css/owl.carousel.min.css',
            '/theme_diva/static/src/css/animate.min.css',
            '/theme_diva/static/src/css/owl.theme.default.min.css',
            '/theme_diva/static/src/js/acLazyLoadImage.js',
            '/theme_diva/static/src/js/owl.carousel.js',
            '/theme_diva/static/src/js/owl.carousel.min.js',
            '/theme_diva/static/src/js/index_layout.js',
            '/theme_diva/static/src/js/popular_product.js',
            '/theme_diva/static/src/js/blog.js',
            '/theme_diva/static/src/js/diva_index.js',
            '/theme_diva/static/src/js/featured_product2.js',
            '/theme_diva/static/src/js/script.js',
            '/theme_diva/static/src/js/featured_product.js',
            '/theme_diva/static/src/js/home_index.js,',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
