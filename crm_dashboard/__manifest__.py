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
    'name': "CRM Dashboard",
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Get a visual report of CRM through a Dashboard in CRM""",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['crm', 'sale', 'sale_crm'],
    'data': ['views/crm_dashboard_views.xml',
             'views/res_users_views.xml',
             'views/utm_campaign_views.xml',
             'views/crm_team_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            'web/static/lib/Chart/Chart.js',
            'crm_dashboard/static/src/css/style.css',
            'crm_dashboard/static/src/js/crm_dashboard.js',
            'crm_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
