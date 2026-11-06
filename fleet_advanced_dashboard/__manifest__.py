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
    "name": "Fleet Dashboard",
    "version": "18.0.1.0.0",
    "category": "Human Resources/Fleet",
    "summary": """Easily analyze, track, and visualize fleet operations and costs""",
    "description": """The Fleet Advanced Dashboard provides an interactive and visual overview of fleet operations. 
     It features dynamic filtering by date, driver, vehicle model, and manufacturer, along with summarized metrics and graphical representations for odometer readings, service costs, recurring contract costs, service types, and vehicle status.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["fleet"],
    "data": ["views/fleet_advanced_dashboard_menus.xml"],
    'assets': {
        'web.assets_backend': [
            "fleet_advanced_dashboard/static/src/js/fleet_dashboard.js",
            "fleet_advanced_dashboard/static/src/xml/fleet_dashboard_templates.xml",
            "fleet_advanced_dashboard/static/src/css/fleet_dashboard.css",
        ],
    },
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
