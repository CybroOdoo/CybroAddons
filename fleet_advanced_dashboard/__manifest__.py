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
{
    "name": "Fleet Dashboard",
    'version': '20.0.1.0.0',
    "category": "Industries,Productivity",
    "summary": """Analyze fleet operations and vehicle metrics with an interactive dashboard""",
    "description": """This module provides an interactive fleet dashboard with graphical insights into odometer readings, service costs, vehicle status, and contract renewals.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["fleet", "web"],
    "data": ["views/fleet_advanced_dashboard_menus.xml"],
    "assets": {
        "web.assets_backend": [
            "fleet_advanced_dashboard/static/src/xml/fleet_dashboard_templates.xml",
            "fleet_advanced_dashboard/static/src/js/fleet_dashboard.js",
            "fleet_advanced_dashboard/static/lib/loader.js",
            "fleet_advanced_dashboard/static/src/css/fleet_dashboard.css"
        ],
    },
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
