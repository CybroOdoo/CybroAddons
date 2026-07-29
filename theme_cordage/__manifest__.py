# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: SANJAY P (odoo@cybrosys.com)
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
    "name": "Cordage Theme",
    "version": "17.0.1.0.0",
    "category": "Theme",
    "summary": "Industrial rope and rigging website theme for Odoo 17",
    "description": "Premium industrial rope and rigging website theme designed for Odoo 17. Features customizable sections, optimized shop layouts, and contact forms.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["website", "website_sale", "website_crm"],
    "data": [
        "views/snippets.xml",
        "views/options.xml",
        "views/website_footer.xml",
        "views/contactus_thankyou.xml",
        "views/website_templates.xml",
        "views/shop_templates.xml",
        "views/product_templates.xml",
        "views/contactus_templates.xml",
        "data/theme_website_menu_data.xml",
    ],
    "demo": [
        "demo/shop_filter_data.xml",
        "demo/theme_demo_products.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "theme_cordage/static/src/js/theme.js",
            "theme_cordage/static/src/js/cart.js",
            "theme_cordage/static/src/scss/theme.scss",
        ],
    },
    "images": [
    	'static/description/banner.jpg',
    	'static/description/theme_screenshot.jpg',
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
