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
    'name': 'Oil & Gas Custody Transfer',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Midstream',
    'summary': 'Custody Transfer workflow, ownership, approvals and audit for Oil ERP',
    'description': """

This module provides a legal and operational workflow layer above inventory
movement. It manages custody, ownership and operator responsibility separately,
applies a configurable approval workflow, and links into existing stock,
accounting and gate pass operations without inheriting them.

Key Features:
- Configurable custody transfer types (internal, external, intercompany,
  truck dispatch, pipeline, commercial sale)
- Separation of legal owner, custodian, operator and carrier
- Multi-party tracking (seller, buyer, transporter, operator, customer)
- Workflow with approvals, in-progress, completion, cancellation and dispute
- Planned vs actual quantity tracking with losses, gains and variance
- Stock picking linkage (no inheritance) and accounting entry hooks
- Gate pass and pipeline linkage
- Full audit trail of approvals, status changes, overrides and disputes
    
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'mail',
        'stock',
        'account',
        'oil_erp_base',
        'oil_erp_transfers',
        'oil_erp_contract',
        'oil_erp_gate_pass',
        'oil_erp_pipeline',
        'oil_erp_hpc_standard',
    ],
    'data': [
        'security/oil_custody_transfer_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/custody_transfer_party_views.xml',
        'views/custody_transfer_event_views.xml',
        'views/custody_transfer_views.xml',
        'views/stock_picking_views.xml',
        'views/custody_transfer_menus.xml',
        'views/pivot_graph_views.xml',
        'wizard/custody_transfer_reporting_wizard_views.xml',
        'report/custody_transfer_pivot_graph_views.xml',
        'report/custody_transfer_report_views.xml',
    ],
    'demo': [
        'demo/custody_transfer_demo.xml',
    ],
    'images': [
            'static/description/banner.jpg',
        ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
