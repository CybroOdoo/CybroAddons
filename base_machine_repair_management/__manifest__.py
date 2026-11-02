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
    'name': 'Machine Repair Management',
    'version': '20.0.1.0.0',
    'category': 'Sales,Website ,Human Resources ,Project',
    'summary': 'Manage machine repair requests, diagnoses, work orders and '
               'repair teams.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr', 'mail', 'portal', 'project', 'sale', 'website'],
    'data': [
        'security/base_machine_repair_management_groups.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_data.xml',
        'data/portal_entry_data.xml',
        'report/repair_report_templates.xml',
        'report/machine_repair_report.xml',
        'views/customer_portal_templates.xml',
        'views/customer_review_templates.xml',
        'views/machine_diagnosis_views.xml',
        'views/machine_repair_views.xml',
        'views/machine_service_type_views.xml',
        'views/machine_service_views.xml',
        'views/machine_workorder_views.xml',
        'views/product_product_views.xml',
        'views/repair_team_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/website_repair_templates.xml',
        'wizard/repair_report_views.xml',
        'views/base_machine_repair_management_menus.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
