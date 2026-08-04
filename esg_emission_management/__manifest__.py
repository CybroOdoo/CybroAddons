# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    "name": "ESG Management",
    "version": "19.0.1.0.0",
    "category": "Sustainability",
    "summary": "Track, measure, and report Enviro metrics — Environmental, Social, Governance",
    "description": """
Enviro Management provides a full Enviro workflow for Odoo:
configure emission factors, log emission records by scope, manage reporting periods,
track reduction targets and initiatives, record offset credits, and report
emissions by scope, category, period, and site.
    
Phase 1: Foundation — security groups (User, Manager, Auditor), reporting periods,
and site/facility hierarchy.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["base", "mail", "account", "uom", "fleet", "hr"],
    "data": [
        "security/enviro_security.xml",
        "security/ir.model.access.csv",
        "data/enviro_gas_data.xml",
        "data/enviro_emission_factor_data.xml",
        "data/enviro_activity_type_data.xml",
        "views/account_move_views.xml",
        "views/enviro_gas_views.xml",
        "views/enviro_activity_type_views.xml",
        "views/enviro_factor_rule_views.xml",
        "views/enviro_emission_factor_views.xml",
        "views/enviro_reporting_period_views.xml",
        "views/enviro_site_views.xml",
        "views/enviro_emission_record_views.xml",
        "views/enviro_emission_record_fleet_views.xml",
        "views/enviro_target_views.xml",
        "views/enviro_initiative_views.xml",
        "views/enviro_offset_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/fleet_commuting_wizard_views.xml",
        "report/enviro_report_templates.xml",
        "report/enviro_report_actions.xml",
        "views/enviro_menus.xml",
    ],
    "demo": [
        "demo/enviro_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "esg_emission_management/static/src/js/enviro_dashboard.js",
            "esg_emission_management/static/src/xml/enviro_dashboard.xml",
            "esg_emission_management/static/src/scss/enviro_dashboard.scss",
        ],
    },
    "license": "LGPL-3",
    'images': [
        'static/description/banner.jpg'],
    "installable": True,
    "application": True,
    "auto_install": False
}
