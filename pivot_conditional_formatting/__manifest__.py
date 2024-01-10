# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
#    """manifest"""
{
    "name": "Conditional Formatting in Pivot View",
    "version": "16.0.1.0.0",
    "category": "Extra Tools",
    "summary": "This Module allows to setup conditional formatting in "
    "the pivot view of models",
    "description": "The module is used for using conditional formatting option"
    "in the pivot view of different models, you can setup"
    " default formatting rules in the settings or add new rules"
    " from the UI.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["base", "web"],
    "data": [
        "security/pivot_conditional_formatting_groups.xml",
        "security/pivot_conditional_settings_security.xml",
        "security/ir.model.access.csv",
        "views/pivot_conditional_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pivot_conditional_formatting/static/src/xml/pivot_conditional_formatting.xml",
            "pivot_conditional_formatting/static/src/css/pivot_conditional_formatting.css",
            "pivot_conditional_formatting/static/src/js/pivot_conditional_formatting.js",
        ],
    },
    "images": ["static/description/banner.png"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
