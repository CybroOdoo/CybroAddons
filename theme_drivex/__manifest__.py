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
    "name": "Theme DriveX",
    "version": "17.0.1.0.0",
    "category": "Theme/Corporate",
    "sequence": 100,
    "summary": "A premium car rental website theme for Odoo 17.",
    "description": """
        Theme DriveX - Premium Car Rental Website Theme for Odoo 17.
        Transform your car rental business with Theme DriveX, 
        a sophisticated and feature-rich theme designed specifically 
        for Odoo 17. This premium theme offers a complete solution for 
        creating a stunning car rental website with seamless
         integration with Odoo's fleet management.
        """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["website", "fleet", "sale_management", "crm"],
    "data": [
        "security/ir.model.access.csv",
        "data/fleet_rental_addon_data.xml",
        "data/fleet_rental_insurance_data.xml",
        "data/fleet_rental_location_data.xml",
        "data/ir_sequence_data.xml",
        "data/mail_template_data.xml",
        "data/website_menu_data.xml",
        "views/fleet_rental_order_views.xml",
        "views/fleet_vehicle_feature_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/layout_templates.xml",
        "views/snippets/snippet_groups.xml",
        "views/snippets/drivex_hero.xml",
        "views/snippets/drivex_stats_bar.xml",
        "views/snippets/drivex_fleet_section.xml",
        "views/snippets/drivex_features.xml",
        "views/snippets/drivex_how_it_works.xml",
        "views/snippets/drivex_reviews.xml",
        "views/snippets/drivex_cta_banner.xml",
        "views/snippets/drivex_vehicle_specs.xml",
        "views/snippets/drivex_vehicle_features.xml",
        "views/snippets/drivex_vehicle_about.xml",
        "views/snippets/drivex_rental_terms.xml",
        "views/snippets/drivex_similar_vehicles.xml",
        "views/snippets/drivex_about_sections.xml",
        "views/snippets/drivex_contact_sections.xml",
        "views/snippets/drivex_booking_sections.xml",
        "views/home_templates.xml",
        "views/fleet_templates.xml",
        "views/services_templates.xml",
        "views/about_templates.xml",
        "views/contact_templates.xml",
        "views/booking_templates.xml",
        "views/car_detail_templates.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            "theme_drivex/static/src/scss/primary_variables.scss",
        ],
        "web.assets_frontend": [
            "theme_drivex/static/src/scss/theme.scss",
            "theme_drivex/static/src/js/theme.js",
        ],
    },
    "images": ['static/description/banner.jpg',
               'static/description/theme_screenshot.jpg', ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
