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
    'name': 'Odoo AI Dynamic Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Build dashboards by drag and drop, or with AI, on any data',
    'description': """
Dynamic Dashboard
=================

Build dashboards without code, right in Odoo:

* A drag and drop builder with 17 building blocks: KPI tiles, progress bars, gauges,
  bar, line, area, pie and radar charts, ranking and pivot tables, record lists,
  embedded Odoo views and texts
* Blocks computed live on any model, with their own filters, measures and groupings
* Automatic arrangement of the blocks, and a menu item for each dashboard
* Personal or shared dashboards, and filters on each block for each viewer
* Dashboards generated from a description, and analyses of blocks, by Odoo's AI service
* Presentation as slides and export as PDF
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'iap'],
    'data': [
        'security/odoo_dynamic_dashboard_security.xml',
        'security/ir.access.csv',
        'views/dynamic_dashboard_block_views.xml',
        'views/dynamic_dashboard_views.xml',
        'views/odoo_dynamic_dashboard_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_dynamic_dashboard/static/src/**/*.scss',
            'odoo_dynamic_dashboard/static/src/**/*.js',
            'odoo_dynamic_dashboard/static/src/**/*.xml',
        ],
        'web.assets_unit_tests': [
            'odoo_dynamic_dashboard/static/tests/**/*.test.js',
        ],
    },
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
