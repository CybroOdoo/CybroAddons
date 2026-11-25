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
    "name": "Conditional Formatting in Pivot View",
    "version": "20.0.1.0.0",
    "category": "Extra Tools",
    "summary": "Set up conditional formatting in pivot views of models",
    "description": "The module is used for using conditional formatting option"
                   "in the pivot view of different models, you can setup"
                   " default formatting rules in the settings or add new rules"
                   " from the UI.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["web"],
    "data": [
        "security/pivot_conditional_formatting_groups.xml",
        "security/ir.access.csv",
        "views/pivot_conditional_settings_views.xml",
    ],
    "assets": {
        'web.assets_backend_lazy': [
            "pivot_conditional_formatting/static/src/xml/pivot_conditional_formatting.xml",
            "pivot_conditional_formatting/static/src/css/pivot_conditional_formatting.css",
            "pivot_conditional_formatting/static/src/js/pivot_conditional_formatting.js",
        ],
    },
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    'auto_install': False,
    'application': False,
}
