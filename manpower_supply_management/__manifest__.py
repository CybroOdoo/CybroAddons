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
    'name': 'Manpower Supply Management',
    'version': '20.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manage manpower supply and worker allocation for customers',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'website', 'account', 'portal'],
    'data': [
        'security/manpower_supply_management_security.xml',
        'security/labour_supply_security.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/labour_supply_website_menu.xml',
        'data/ir_cron_data.xml',
        'data/portal_entry_data.xml',
        'views/workers_details_views.xml',
        'views/skill_details_views.xml',
        'views/labour_supply_views.xml',
        'views/labour_on_skill_views.xml',
        'views/labour_on_supply_form_template.xml',
        'views/labour_supply_portal_templates.xml',
        'views/labour_supply_dashboard_views.xml',
        'wizard/labour_supply_report_views.xml',
        'report/labour_supply_templates.xml',
        'report/labour_supply_reports.xml',
        'report/form_print_labour_supply_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/manpower_supply_management/static/src/js/lib/Chart.bundle.js',
            '/manpower_supply_management/static/src/js/labour_supply_dashboard.js',
            '/manpower_supply_management/static/src/css/dashboard.css',
            '/manpower_supply_management/static/src/scss/dashboard.scss',
            '/manpower_supply_management/static/src/xml/labour_supply_dashboard.xml',
        ],
        'web.assets_frontend': [
            '/manpower_supply_management/static/src/css/website.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
