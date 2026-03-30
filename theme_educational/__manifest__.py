# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
    'name': 'Theme Educational',
    'description': 'Theme Educational is an attractive and modern eCommerce Website theme',
    'summary': 'Design Web Pages with theme Education',
    'category': 'Theme/eCommerce',
    'version': '18.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_blog', 'website_sale', 'payment_demo', 'website_sale_wishlist', 'website_slides'],
    'data': [
        'data/about_us_data.xml',
        'views/header_templates.xml',
        'views/footer_template.xml',
        'views/contactus_template.xml',
        'views/blog_template.xml',
        'views/checkout_template.xml',
        'views/cart_template.xml',
        'views/about_us_template.xml',
        'views/search_course_snippet.xml',
        'views/choose_a_ctegory_snippet.xml',
        'views/choose_a_paln_snippet.xml',
        'views/faq_snippet.xml',
        'views/product_snippet_view.xml',
        'views/website_shop_view.xml',
        'views/product_detail_view.xml',
        'views/all_courses_view.xml',
        'views/home_page_view.xml',
        'views/popular_courses_view.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            '/theme_educational/static/src/css/owl.carousel.min.css',
            '/theme_educational/static/src/css/owl.theme.default.min.css',
            '/theme_educational/static/src/css/style.css',
            '/theme_educational/static/src/xml/top_trending_courses_snippet.xml',
            '/theme_educational/static/src/js/carousal_swipe.js',
            '/theme_educational/static/src/js/owl.carousel.js',
            '/theme_educational/static/src/js/highlight.js',
            '/theme_educational/static/src/js/popular_courses.js',
            '/theme_educational/static/src/js/award_and_stuff_carousal.js',
            '/theme_educational/static/src/xml/award_and_stuff.xml'
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
