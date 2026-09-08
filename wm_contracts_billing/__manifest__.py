# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Waste Management Contracts & Billing',
    'version': '19.0.1.0.0',
    'category': 'Sales/Billing',
    'summary': 'Customer Contracts, SLAs, Portal & Consolidated Billing for Waste Management',
    'description': """
        Waste Management Contracts & Billing Module.
        Consolidates customer portal, customer contract management, service level agreements (SLAs),
        rate cards, contract-based pricing, monthly billing runs, and consolidated invoicing.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Technologies Pvt. Ltd.',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'wm_base',
        'wm_collection',
        'contacts',
        'mail',
        'product',
        'account',
        'portal',
        'crm',
        'sale',
        'website',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'data': [
        'security/wm_customer_security.xml',
        'security/wm_billing_security.xml',
        'security/ir.model.access.csv',
        'reports/partner_contract_report.xml',
        'reports/partner_contract_report_template.xml',
        'reports/pricing_rule_summary_actions.xml',
        'reports/pricing_rule_summary_template.xml',
        'data/ir_sequence_data.xml',
        'data/partner_contract_sequence.xml',
        'data/mail_template_contract.xml',
        'data/ir_cron.xml',
        'data/ir_cron_data.xml',
        'wizards/wm_sla_send_email_wizard_views.xml',
        'wizards/wm_lead_conversion_wizard_views.xml',
        'wizards/wm_consolidated_billing_wizard_views.xml',
        'wizards/wm_pricing_rule_summary_wizard_views.xml',
        'wizards/wm_monthly_billing_wizard_views.xml',
        'views/contract_line_views.xml',
        'views/partner_contract_views.xml',
        'views/wm_partner_contract_views.xml',
        'views/partner_contract_menu.xml',
        'views/wm_sla_views.xml',
        'views/wm_customer_profitability_report_views.xml',
        'views/res_partner_views.xml',
        'views/wm_driver_domain_views.xml',
        'views/crm_lead_views.xml',
        'views/sale_order_views.xml',
        'views/portal_templates.xml',
        'views/wm_pricing_rule_views.xml',
        'views/wm_consolidated_invoice_views.xml',
        'views/wm_monthly_billing_run_views.xml',
        'views/wm_revenue_report_views.xml',
        'views/wm_weight_revenue_report_views.xml',
        'views/wm_operations_report_views.xml',
        'views/wm_collection_order_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_customers.xml',
        'demo/demo_contracts.xml',
        'demo/demo_monthly_billing_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'wm_contracts_billing/static/src/css/collection_dashboard.css',
            'wm_contracts_billing/static/src/css/portal_download.css',
            'wm_contracts_billing/static/src/js/portal_download.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
