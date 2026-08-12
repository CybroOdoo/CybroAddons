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
# ############################################################################

{
    'name': 'Oil & Gas ARO and Decommissioning',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Finance',
    'summary': 'IAS 37 Asset Retirement Obligations, EIM accretion, pipeline segments, JV cost-sharing, multi-currency WIP and partial settlement',
    'description': """
    
Manage Asset Retirement Obligations (ARO) and decommissioning activities with liability recognition,
accretion, settlement tracking, and multi-currency support. Integrates with reservoirs, leases, equipment, projects, JV agreements,
 and ESG workflows while providing automated compliance, alerts, and audit tracking.
 
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'oil_erp_reservoir',
        'oil_erp_project',
        'oil_erp_lease',
        'oil_erp_equipment',
        'oil_erp_jv',
        'oil_erp_esg',
        'account',
        'project',
        'maintenance',
        'mail',
    ],
    'data': [
        'security/oil_aro_security.xml',
        'security/ir.model.access.csv',
        'data/aro_sequence_data.xml',
        'data/aro_cron_data.xml',
        'data/aro_mail_template_data.xml',
        'wizard/aro_revision_views.xml',
        'wizard/aro_settlement_views.xml',
        'views/oil_aro_obligation_views.xml',
        'views/oil_aro_wip_views.xml',
        'views/oil_reservoir_views.xml',
        'views/oil_lease_agreement_views.xml',
        'views/project_project_views.xml',
        'views/oil_aro_template_views.xml',
        'views/oil_aro_menus.xml',
        'views/oil_bulk_schedule_template_views.xml',
        'views/pivot_graph_views.xml',
    ],
    'images': [
            'static/description/banner.jpg',
        ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
