# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raneesha MK (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
{
    "name": "Website Fleet Service",
    "version": "17.0.1.0.0",
    "category": "Industries, Website",
    "summary": """Car service through Website""",
    "description": """This module helps Users to book the Car services through
     online.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["website", "fleet_car_workshop"],
    "data": [
        "security/website_fleet_service_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/service_type_data.xml",
        "data/website_fleet_service_menu_data.xml",
        "views/service_booking_views.xml",
        "views/service_package_views.xml",
        "views/service_type_views.xml",
        "views/service_worksheet_views.xml",
        "views/website_service_booking_templates.xml",
        "views/website_service_package_templates.xml",
        "views/website_service_booking_portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_fleet_service/static/src/css/website_service.css",
            "website_fleet_service/static/src/js/website_service.js",
        ],
    },
    "images": ["static/description/banner.jpg"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
