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
    'name': 'Queue Manager',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Manage customer queue, token generation, and counter operations',
    'description': 'A simple queue management system with token generation, department-wise queues, and counter processing.',
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'website'],
    'data': [
        'security/security.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/website_menu_data.xml',
        'views/token_interface_views.xml',
        'views/generate_token_template.xml',
        'views/department_views.xml',
        'views/token_session_views.xml',
        'views/token_token_views.xml',
        'views/queue_counter_views.xml',
        'views/queue_process_views.xml',
        'views/queue_display_views.xml',
        'views/dashboard_actions.xml',
        'report/token_report_templates.xml',
        'wizard/select_department_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_queue_manager/static/src/css/styles.css',
        ],
        'web.assets_backend': [
            'odoo_queue_manager/static/src/css/dashboard.css',
            'odoo_queue_manager/static/src/js/dashboard.js',
            'odoo_queue_manager/static/src/xml/queue_management_dashboard_template.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True
}
