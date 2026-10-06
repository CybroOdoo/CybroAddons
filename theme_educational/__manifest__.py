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
    'version': '17.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Design Web Pages with theme Education',
    'description': 'Theme Educational is an attractive and modern eCommerce Website theme',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'website',
        'website_blog',
        'website_sale',
        'website_sale_wishlist',
        'website_slides',
        'payment_demo',
    ],
    'data': [
        'data/about_us_data.xml',
        'views/header_templates.xml',
        'views/footer_templates.xml',
        'views/home_page_templates.xml',
        'views/about_us_templates.xml',
        'views/contactus_templates.xml',
        'views/all_courses_templates.xml',
        'views/popular_courses_templates.xml',
        'views/website_shop_templates.xml',
        'views/product_detail_templates.xml',
        'views/cart_templates.xml',
        'views/checkout_templates.xml',
        'views/blog_templates.xml',
        'views/search_course_snippet.xml',
        'views/choose_a_plan_snippet.xml',
        'views/faq_snippet.xml',
        'views/product_snippet_templates.xml',
        'views/choose_a_category_snippet.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_educational/static/src/css/owl.carousel.min.css',
            'theme_educational/static/src/css/owl.theme.default.min.css',
            'theme_educational/static/src/css/style.css',
            'theme_educational/static/src/js/owl.carousel.js',
            'theme_educational/static/src/js/highlight.js',
            'theme_educational/static/src/js/carousel_swipe.js',
            'theme_educational/static/src/js/popular_courses.js',
            'theme_educational/static/src/js/award_and_stuff_carousel.js',
            'theme_educational/static/src/js/contact_phone_input.js',
            'theme_educational/static/src/xml/top_trending_courses_snippet.xml',
            'theme_educational/static/src/xml/award_and_stuff.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
