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
    'name': 'Oil & Gas Joint Venture',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Upstream',
    'summary': 'Joint Operating Agreements, AFEs, Cash Calls & Joint Interest Billing',
    'description': """
Oil & Gas Joint Venture Management
====================================
Full Joint Venture accounting for Oil & Gas operations:
- Joint Operating Agreements (JOA) with Working Interest validation
- JV Partner management with WI% per partner
- Authority for Expenditure (AFE) with partner approval workflow
- Monthly Cash Calls that auto-generate Odoo invoices per partner
- Joint Interest Billing (JIB) splitting actual costs by WI%
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'oil_erp_project',
        'oil_erp_reservoir',
        'oil_erp_royalty',
        'oil_erp_contract',
        'account',
        'mail',
    ],
    'data': [
        'security/oil_jv_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/oil_jv_agreement_views.xml',
        'views/oil_jv_partner_views.xml',
        'views/oil_afe_views.xml',
        'views/oil_jv_cash_call_views.xml',
        'views/oil_jv_jib_views.xml',
        'views/oil_jv_revenue_views.xml',
        'views/project_project_views.xml',
        'views/oil_reservoir_views.xml',
        'views/oil_contract_views.xml',
        'views/oil_royalty_views.xml',
        'views/oil_jv_menus.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}