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
    'name': 'CRM Kit',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Comprehensive CRM suite with sales commission plans and team management for Odoo 20',
    'description': """CRM Kit brings advanced sales management capabilities to Odoo 20.
    It provides tiered and graduated commission plans, salesperson performance tracking,
    team management, and detailed commission reporting with XLSX export.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'crm', 'crm_dashboard'],
    'data': [
        'security/ir.access.csv',
        'views/crm_commission_views.xml',
        'views/crm_team_views.xml',
        'views/res_users_views.xml',
        'wizard/commission_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'crm_kit/static/src/js/action_manager.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
