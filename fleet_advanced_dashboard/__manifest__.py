# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
    "name": "Fleet Dashboard",
    "version": "16.0.1.0.0",
    "category": "Industries,Productivity",
    "summary": """User can analyse the fleet module in easy ways """,
    "description": """In this module can see all tha data related to the fleet 
     module. Flee dashboard contain the graphical representation of the odometer
     values, service cost, vehicle status and service types""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["base", "hr", "fleet"],
    "data": ["views/fleet_advanced_dashboard_menus.xml"],
    "assets": {
        "web.assets_common": [
            "fleet_advanced_dashboard/static/src/css/fleet_dashboard.css",
        ],
        "web.assets_backend": [
            "fleet_advanced_dashboard/static/src/xml/fleet_dashboard_templates.xml",
            "fleet_advanced_dashboard/static/src/js/fleet_dashboard.js",
            "https://www.gstatic.com/charts/loader.js",
        ],
    },
    "images": ["static/description/banner.png"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
