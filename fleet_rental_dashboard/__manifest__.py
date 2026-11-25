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
    'name': 'Fleet Rental Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Dashboard for fleet rental management',
    'description': 'This dashboard module enhances the fleet rental management '
                   'system by offering a centralized view of crucial metrics'
                   ' and analytics.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['fleet_rental'],
    'data': ['views/fleet_rental_dashboard_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            'fleet_rental_dashboard/static/src/js/dashboard.js',
            'fleet_rental_dashboard/static/src/css/dashboard.css',
            'fleet_rental_dashboard/static/src/css/style.scss',
            'fleet_rental_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
