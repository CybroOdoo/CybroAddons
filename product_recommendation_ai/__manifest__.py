# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Product Recommendation AI",
    'version': "18.0.1.0.0",
    'category': "eCommerce",
    'summary': "AI-powered product recommendations with multiple performance options",
    'description': """This module provides an AI-driven product recommendation system in Odoo. 
    It allows users to recommend products to customers based on semantic similarity 
    using either a high-speed or high-performance embedding model. 
    Multiple product metadata such as name, description, tags, and category are used 
    to generate embeddings. Customers can choose performance or speed-based recommendations.""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends':['base','website','website_sale','sale'],
    'data':[
        "views/res_config_settings_views.xml",
        "views/recommended_product_snippet_carousel.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'product_recommendation_ai/static/src/js/product_recommending.js',
            'product_recommendation_ai/static/src/js/product_carousel.js',
            'product_recommendation_ai/static/src/css/product_recommend_slider.css',
        ],
    },
    'images': ['static/description/Banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
