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
#############################################################################
{
    'name': 'Franchise Management',
    'version': '20.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Manage franchisees, dealer applications, contracts, and sales performance in Odoo.',
    'description': """This module helps to manage the franchise in Odoo.
A franchise is a type of license that grants a franchisee access, thus
allowing the franchisee to sell a product or service under the franchise's
business name.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['portal', 'website'],
    'data': [
        'security/franchise_management_security.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/contract_email_data.xml',
        'data/franchise_contract_data.xml',
        'data/contract_renewal_email_data.xml',
        'data/feedback_email_data.xml',
        'data/monthly_feedback_cron_data.xml',
        'data/contract_renewal_cron_data.xml',
        'report/franchise_dealership_contract_templates.xml',
        'report/franchise_management_report.xml',
        'report/franchise_report_templates.xml',
        'report/dealer_based_templates.xml',
        'report/dealer_sale_report_templates.xml',
        'report/dealer_sale_based_templates.xml',
        'report/agreement_based_templates.xml',
        'report/dealer_sale_on_agreement_templates.xml',
        'wizard/dealer_report_views.xml',
        'wizard/dealer_sale_report_views.xml',
        'views/franchise_dealer_views.xml',
        'views/web_franchise_templates.xml',
        'views/franchise_agreement_views.xml',
        'views/approved_dealer_views.xml',
        'views/res_users_views.xml',
        'views/franchise_dealer_portal_templates.xml',
        'views/franchise_dealer_portal_detail_templates.xml',
        'views/franchise_sales_views.xml',
        'views/web_franchise_sales_templates.xml',
        'views/franchise_management_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'franchise_management/static/src/css/website.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
