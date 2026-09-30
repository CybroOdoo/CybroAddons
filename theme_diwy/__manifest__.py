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
    "name": "Theme Diwy",
    "version": "17.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Diwy Backend Theme is an attractive theme for Odoo backend",
    "description": """Minimalist and elegant theme for Odoo backend""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["web", "mail"],
    "data": [
        "views/login_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "theme_diwy/static/src/xml/menu_panels.xml",
            "theme_diwy/static/src/xml/nav_bar_panel.xml",
            "theme_diwy/static/src/xml/home_menus.xml",
            "theme_diwy/static/src/xml/side_bar_panel.xml",
            "theme_diwy/static/src/scss/nav.scss",
            "theme_diwy/static/src/scss/sidebar.scss",
            "theme_diwy/static/src/css/style.css",
            "theme_diwy/static/src/js/home_menus.js",
            "theme_diwy/static/src/js/search_apps.js",
        ],
        "web.assets_frontend": [
            "theme_diwy/static/src/scss/login.scss",
        ],
    },
    "images": [
        "static/description/banner.jpg",
        "static/description/theme_screenshot.jpg",
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
