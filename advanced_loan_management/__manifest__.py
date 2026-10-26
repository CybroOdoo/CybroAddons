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
    'name': 'Advanced Loan Management',
    'version': '20.0.1.0.0',
    'summary': 'Helps You To Manage Loan Requests/Disbursement/'
               'Repayments/Amortization Operations',
    'description': 'Module allows creating different types of loans, '
                   'managing loan requests and amortization operations simply, '
                   'and creating invoices for each repayment amount.',
    'category': 'Accounting',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'account', 'base'],
    'data': [
        'security/loan_management_groups.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/loan_journal_data.xml',
        'views/loan_type_views.xml',
        'views/loan_request_views.xml',
        'views/repayment_lines_views.xml',
        'views/loan_documents_views.xml',
        'views/res_config_settings_views.xml',
        'views/loan_management_menus.xml',
        'views/res_partner_views.xml',
        'wizard/message_popup_views.xml',
        'wizard/reject_reason_views.xml',
        'report/loan_management_reports.xml',
        'report/loan_report_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
