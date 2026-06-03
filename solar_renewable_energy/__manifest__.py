# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amrithesh K (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Solar Renewable Energy",
    'version': '17.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Manage solar renewable energy projects from lead to installation and maintenance.',
    'description': "This module provides a complete solution for managing solar renewable energy projects. "
                   "Users can capture leads, schedule site inspections, and create project orders. "
                   "The system enables real-time tracking of installations, subcontractor management, and "
                   "post-installation maintenance workflows. Ideal for companies handling residential, "
                   "commercial, or industrial solar energy deployments.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'product', 'crm', 'sale_management', 'mrp', 'purchase', 'maintenance'],
    'data': [
        'security/solar_renewable_energy_groups.xml',
        'security/solar_renewable_energy_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/service_type_views.xml',
        'views/property_type_views.xml',
        'views/contract_demand_views.xml',
        'views/customer_category_views.xml',
        'views/crm_lead_views.xml',
        'views/survey_team_views.xml',
        'views/installation_team_views.xml',
        'views/installation_team_task_views.xml',
        'views/quality_assurance_team_views.xml',
        'views/quality_assurance_team_task_views.xml',
        'views/subcontract_installation_team_task_views.xml',
        'views/subcontract_quality_assurance_team_task_views.xml',
        'views/site_inspection_views.xml',
        'views/ren_order_views.xml',
        'views/res_partner_views.xml',
        'views/maintenance_request_views.xml',
        'views/mrp_bom_views.xml',
        'views/renewable_energy_menu_views.xml',
        'wizard/site_inspection_assignment_views.xml',
    ],
    'assets': {
        "web.chartjs_lib": [
            '/web/static/lib/Chart/Chart.js',
            '/web/static/lib/chartjs-adapter-luxon/chartjs-adapter-luxon.js',
        ],
        'web.assets_backend': [
            'solar_renewable_energy/static/src/js/dashboard.js',
            'solar_renewable_energy/static/src/css/dashboard.css',
            'solar_renewable_energy/static/src/xml/dashboard.xml'
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
