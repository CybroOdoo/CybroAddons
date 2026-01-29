# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
    'name': 'Theme Eco Refine',
    'version': '15.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Theme Eco Refine Front-end theme',
    'description': 'Theme includes attractive and modern dynamic/static'
                   ' snippets for your website pages',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ['website_livechat',
                'website_sale_wishlist', 'website_blog'],
    'data': [
        'views/theme_refurbished_menus.xml',
        'views/templates.xml',
        'views/product_template_views.xml',
        'views/website_blog_templates.xml',
        'views/about_us_templates.xml',
        'static/src/xml/homepage_templates.xml',
        'views/snippets/website_snippets_inherits.xml',
        'static/src/xml/best_seller_snippet_templates.xml',
        'static/src/xml/new_arrival_snippet_templates.xml',
        'static/src/xml/top_rated_product_snippet_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_eco_refine/static/src/css/contact_us.css',
            'theme_eco_refine/static/src/css/product.css',
            'theme_eco_refine/static/src/css/home.css',
            'theme_eco_refine/static/src/css/blog.css',
            'theme_eco_refine/static/src/js/menu.js',
            'theme_eco_refine/static/src/css/about_us.css',
            'theme_eco_refine/static/src/js/about_us.js',
            'theme_eco_refine/static/src/js/owl.carousel.js',
            'theme_eco_refine/static/src/js/owl.carousel.min.js',
            'theme_eco_refine/static/src/css/owl.carousel.css',
            'theme_eco_refine/static/src/js/collection_snippet.js',
            'theme_eco_refine/static/src/js/refurbished_carousel_'
            'snippet.js',
            'theme_eco_refine/static/src/js/best_seller_snippet.js',
            'theme_eco_refine/static/src/js/new_arrival_snippet.js',
            'theme_eco_refine/static/src/js/customer_response.js',
            'theme_eco_refine/static/src/js/top_rated_products_'
            'snippet.js',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_refurbished.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
