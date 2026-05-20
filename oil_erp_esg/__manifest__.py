# -*- coding: utf-8 -*-
#############################################################################
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
    'name': 'Oil & Gas ESG',
    'version': '19.0.2.0.0',
    'category': 'Industries/Oil & Gas',
    'summary': 'Environmental, Social & Governance Management for Oil & Gas ERP',
    'description': """
Oil ERP ESG Module
==================
Comprehensive ESG (Environmental, Social & Governance) management
tailored for Oil & Gas operations.

Features:
---------
* GHG Emissions Tracking (Scope 1, 2, 3)
* Flaring & Venting Management
* Energy Consumption & Efficiency
* Water & Waste Management
* HSE (Health, Safety & Environment) Incidents
* Workforce Diversity & Social KPIs
* ESG Initiatives & Targets Tracker
* Regulatory Compliance (GHG Protocol, IPIECA, TCFD)
* ESG Dashboard & Reporting
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base',
        'mail',
        'hr',
        'oil_erp_base',
        'oil_erp_project',
        'oil_erp_hse',
        'mrp',
        'stock',
        'delivery',
        'fleet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/esg_emission_views.xml',
        'views/esg_energy_views.xml',
        'views/esg_water_views.xml',
        'views/esg_workforce_views.xml',
        'views/esg_initiative_views.xml',
        'views/esg_compliance_views.xml',
        'views/esg_dashboard_views.xml',
        'views/esg_menus.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
