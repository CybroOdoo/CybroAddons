# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    "name": "Theme Velora",
    "version": "18.0.1.0.0",
    "category": "Theme/eCommerce",
    "summary": "Luxury perfume eCommerce theme for Odoo Website",
    "description": "Velora is a luxury fragrance storefront theme with a refined homepage, animated product showcase, collection sections, testimonials, FAQ, and newsletter interactions.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["website", "website_sale", "website_sale_wishlist", "sale"],
    "data": [
        "data/categories.xml",
        "data/website_menu.xml",
        "views/layout_templates.xml",
        "views/snippets/snippets.xml",
        "views/snippets/options.xml",
        "views/homepage_templates.xml",
        "views/contact_templates.xml",
        "views/about_templates.xml",
        "views/collections_templates.xml",
        "views/bestseller_templates.xml",
        "views/confirmation_templates.xml",
        "views/login_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "theme_velora/static/src/css/style.css",
            "theme_velora/static/src/css/bestseller.css",
            "theme_velora/static/src/css/confirmation.css",
            "theme_velora/static/src/js/theme_velora.js"
        ],
        "website.assets_wysiwyg": [
            "theme_velora/static/src/css/style.css"
        ]
    },
"images": ["static/description/banner.jpg",
                "static/description/theme_screenshot.jpg"],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
