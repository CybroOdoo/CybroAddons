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
#############################################################################
{
    'name': "Product Recommendation AI",
    'version': "20.0.1.0.0",
    'category': "eCommerce",
    'summary': "AI-powered product recommendations with multiple performance options",
    'description': """This module provides an AI-driven product recommendation system for Odoo eCommerce.
    It recommends products to customers based on semantic similarity,
    using either a high-speed local model or a high-performance remote embedding model.
    Product metadata such as name, description, and category is used
    to generate embeddings for personalized product recommendations.""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_sale', 'sale'],
    'data': [
        "views/res_config_settings_views.xml",
        "views/recommended_product_snippet_carousel.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'product_recommendation_ai/static/src/js/product_carousel.js',
            'product_recommendation_ai/static/src/css/product_recommend_slider.css',
        ],
    },
    'external_dependencies': {
        'python': ['numpy'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
