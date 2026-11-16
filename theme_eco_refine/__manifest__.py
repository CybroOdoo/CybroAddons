# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Theme Eco Refine',
    'version': '20.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Theme Eco Refine helps you create an attractive and unique '
               'front-end theme',
    'description': """The Theme Eco Refine module provides an attractive and
    unique front-end theme, mainly suitable for eCommerce websites.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale', 'website_blog', 'sale', 'rating'],
    'data': [
        'data/theme_eco_refine_menus.xml',
        'views/product_template_views.xml',
        'views/website_blog_templates.xml',
        'views/templates.xml',
        'views/homepage_templates.xml',
        'views/about_us_templates.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_eco_refine/static/lib/jquery/jquery.min.js',
            'theme_eco_refine/static/lib/owl.carousel/owl.carousel.js',
            'theme_eco_refine/static/src/css/contact_us.css',
            'theme_eco_refine/static/src/css/product.css',
            'theme_eco_refine/static/src/css/home.css',
            'theme_eco_refine/static/src/css/blog.css',
            'theme_eco_refine/static/src/js/product_specification.js',
            'theme_eco_refine/static/src/css/about_us.css',
            'theme_eco_refine/static/src/js/about_us.js',
            'theme_eco_refine/static/lib/owl.carousel/owl.carousel.css',
            'theme_eco_refine/static/src/js/collection_snippet.js',
            'theme_eco_refine/static/src/js/customer_response.js',
            'theme_eco_refine/static/src/js/best_seller_snippet.js',
            'theme_eco_refine/static/src/xml/best_seller_snippet_templates.xml',
            'theme_eco_refine/static/src/js/new_arrival_snippet.js',
            'theme_eco_refine/static/src/xml/new_arrival_snippet_templates.xml',
            'theme_eco_refine/static/src/js/top_rated_products_snippet.js',
            'theme_eco_refine/static/src/xml/'
            'top_rated_product_snippet_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
