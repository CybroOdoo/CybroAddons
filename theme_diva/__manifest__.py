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
    'name': 'Theme Diva',
    'version': '15.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': ' Elevate Your Online Stores Look and Functionality',
    'description': """Elevate your online store with "Theme Diva." This
     powerful eCommerce theme seamlessly integrates with Odoo, offering a 
     captivating design and user-friendly experience. Showcase your products,
      engage customers, and optimize performance effortlessly.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'website_blog', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_featured_data.xml',
        'views/layout_templates.xml',
        'views/customize_templates.xml',
        'views/header_templates.xml',
        'views/login_templates.xml',
        'views/shop_templates.xml',
        'views/product_templates.xml',
        'views/cart_templates.xml',
        'views/checkout_templates.xml',
        'views/contact_us_templates.xml',
        'views/product_featured_views.xml',
        'views/snippets/index_banner_templates.xml',
        'views/snippets/index_main_product_templates.xml',
        'views/snippets/index_featured_product_templates.xml',
        'views/snippets/index_demo_templates.xml',
        'views/snippets/index_subscribe_templates.xml',
        'views/snippets/banner_templates.xml',
        'views/snippets/popular_product_templates.xml',
        'views/snippets/Featured_product_templates.xml',
        'views/snippets/testimonial_templates.xml',
        'views/snippets/offer_templates.xml',
        'views/snippets/index2_blog_templates.xml',
        'views/snippets/index3_banner_templates.xml',
        'views/snippets/index3_product_templates.xml',
        'views/snippets/index3_store_templates.xml',
        'views/snippets/index3_gallery_templates.xml',
        'views/snippets/index3_blog_templates.xml',
        'views/snippets/landing_features_templates.xml',
        'views/snippets/landing_demo_templates.xml',
        'views/snippets/landing_banner_templates.xml',
        'views/snippets/landing_sponsored_templates.xml',
        'views/snippets/landing_testimonial_templates.xml',
        'views/snippets/landing_subscribe_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/theme_diva/static/src/css/style.css',
            'theme_diva/static/src/css/pluginstyle.css',
            '/theme_diva/static/src/css/owl.carousel.min.css',
            '/theme_diva/static/src/css/animate.min.css',
            '/theme_diva/static/src/css/owl.theme.default.min.css',
            '/theme_diva/static/src/js/acLazyLoadImage.js',
            '/theme_diva/static/src/js/owl.carousel.js',
            '/theme_diva/static/src/js/owl.carousel.min.js',
            '/theme_diva/static/src/js/index2.js',
            '/theme_diva/static/src/js/popular_product.js',
            '/theme_diva/static/src/js/blog.js',
            '/theme_diva/static/src/js/index3.js',
            '/theme_diva/static/src/js/featured_product2.js',
            '/theme_diva/static/src/js/script.js',
            '/theme_diva/static/src/js/featured_product.js',
            '/theme_diva/static/src/js/index.js,',
            '/theme_diva/static/src/js/carousel.js,'
        ],
        'web.assets_qweb': [
            '/theme_diva/static/src/xml/index_main_product_templates.xml',
            '/theme_diva/static/src/xml/index3_blog_templates.xml',
            '/theme_diva/static/src/xml/index2_blog_templates.xml',
            '/theme_diva/static/src/xml/index_featured_products_templates.xml',
            '/theme_diva/static/src/xml/index_featured_products2_templates.xml',
        ]
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
