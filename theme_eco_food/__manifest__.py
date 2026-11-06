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
#############################################################################



# This Cybrosys module is not an OCA module.
# pylint: disable=manifest-required-author

{
    "name": "Theme Eco Food",
    "version": "20.0.1.0.0",
    "summary": "Responsive eCommerce storefront for food and wellness products",
    "category": "Theme/eCommerce",
    'description': 'A longer description of what this theme provides.',
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["website", "website_sale", "website_mass_mailing", "website_blog"],
    "data": [
        "security/ir.access.csv",
        "data/eco_food_snippet_data.xml",
        "views/shop_template.xml",
        "views/best_seller_views.xml",
        "views/recently_added_views.xml",
        "views/featured_product_views.xml",
        "views/new_arrival_views.xml",
        "views/footer_template.xml",
        "views/header_template.xml",
        "views/blog_template.xml",
        "views/contact_template.xml",
        "views/cart_template.xml",
        "views/checkout_template.xml",
        "views/testimonial_views.xml",
        "views/snippets/banner_template.xml",
        "views/snippets/best_seller_template.xml",
        "views/snippets/client_template.xml",
        "views/snippets/featured_product_template.xml",
        "views/snippets/new_arrival_template.xml",
        "views/snippets/recently_added_template.xml",
        "views/snippets/service_template.xml",
        "views/snippets/testimonial_template.xml",
        "views/snippets/website_ad_template.xml",
        "views/snippets/ad_template.xml",
        "views/snippets/snippet_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "theme_eco_food/static/lib/jquery/jquery.min.js",
            "theme_eco_food/static/src/js/jquery.js",
            "theme_eco_food/static/src/xml/snippets/best_seller.xml",
            "theme_eco_food/static/src/xml/snippets/featured_products.xml",
            "theme_eco_food/static/src/xml/snippets/new_arrival_products.xml",
            "theme_eco_food/static/src/xml/snippets/recently_added.xml",
            "theme_eco_food/static/src/xml/snippets/testimonial.xml",
            "theme_eco_food/static/src/css/animate.min.css",
            "theme_eco_food/static/src/css/owl.carousel.min.css",
            "theme_eco_food/static/src/css/owl.theme.default.min.css",
            "theme_eco_food/static/src/css/style.css",
            "theme_eco_food/static/src/scss/style.scss",
            "theme_eco_food/static/src/js/owl.carousel.js",
            "theme_eco_food/static/src/js/script.js",
            "theme_eco_food/static/src/js/index.js",
            "theme_eco_food/static/src/js/new_arrivals.js",
            "theme_eco_food/static/src/js/best_seller.js",
            "theme_eco_food/static/src/js/featured_products.js",
            "theme_eco_food/static/src/js/recently_added.js",
            "theme_eco_food/static/src/js/testimonial.js",
            "theme_eco_food/static/src/js/website_sale.js",
            "theme_eco_food/static/src/js/custom.js",
            "theme_eco_food/static/src/css/wishlist.css",
        ],
    },
    "images": [
        "static/description/banner.jpg",
        "static/description/theme_screenshot.jpg",
    ],
    "license": "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
