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
    'name': 'Warehouse 3D Map & Designer',
    'version': '20.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'Design warehouse layouts on a 2D canvas and explore them in a 3D view with a stock heatmap.',
    'description': """
     Design warehouse layouts visually on an interactive 2D canvas and explore
     them in a 3D WebGL walkthrough. Drag and drop racks, shelves, bins and
     zones onto a grid with snapping, toggle a green-to-red stock density
     heatmap, search for products to fly the camera to where they are stored,
     manage one layout per floor, and customise location shapes and colours.
     Multi-company compatible, and works with Community and Enterprise.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'stock'],
    'data': [
        'security/ir.access.csv',
        'views/warehouse_layout_views.xml',
        'views/stock_location_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'data/stock_location_demo.xml',
        'data/warehouse_layout_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'warehouse_3d_designer/static/src/**/*.js',
            'warehouse_3d_designer/static/src/**/*.scss',
            'warehouse_3d_designer/static/src/**/*.xml',
        ],
        'web.assets_tests': [
            'warehouse_3d_designer/static/tests/tours/**/*',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
