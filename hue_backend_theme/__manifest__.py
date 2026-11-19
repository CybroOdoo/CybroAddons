# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: AMRITHESH K (odoo@cybrosys.com)
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
# This Cybrosys module is not an OCA module.
# pylint: disable=manifest-required-author,missing-module-docstring
{
    "name": "Hue Backend Theme",
    "version": "20.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Hue Backend Theme is an attractive and customizable backend theme for Odoo 20.",
    'description': 'A longer description of what this theme provides.',
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["web", "mail"],
    "data": [
        "views/layout_templates.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hue_backend_theme/static/src/components/app_menu/side_menu.xml",
            "hue_backend_theme/static/src/layout/style/layout_colors.scss",
            "hue_backend_theme/static/src/components/app_menu/menu_order.css",
            "hue_backend_theme/static/src/layout/style/layout_style.scss",
            "hue_backend_theme/static/src/layout/style/sidebar.scss",
            "hue_backend_theme/static/src/components/app_menu/search_apps.js",
        ],
        "web.assets_frontend": [
            "hue_backend_theme/static/src/layout/style/login.scss",
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
