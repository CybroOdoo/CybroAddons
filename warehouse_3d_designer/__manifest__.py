# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Warehouse 3D Map & Designer',
    'version': '17.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'Interactive visual warehouse layout designer with stock '
               'density heatmaps',
    'description': """
                Warehouse 3D Map & Designer
                ============================
                Design your warehouse layouts visually using an interactive canvas.
                Drag and drop racks, shelves, bins, and zones onto a grid.
                Toggle stock density heatmaps to see which areas are full at a glance.
                
                Features:
                - 2D Canvas + 3D WebGL warehouse visualization
                - Switch between 2D design and 3D walkthrough views
                - Drag & drop location placement
                - Grid snapping for clean layouts
                - Stock density heatmap (green to red)
                - 3D racks with shelf details, shadows, and labels
                - Orbit, pan, zoom camera controls in 3D
                - Location detail sidebar
                - Multi-floor/zone support
                - Background floor plan upload
                - Multi-company compatible
                - Works with both Community and Enterprise editions
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock'],
    'data': [
        'security/warehouse_layout_security.xml',
        'security/ir.model.access.csv',
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
            'warehouse_3d_designer/static/lib/three.min.js',
            'warehouse_3d_designer/static/src/**/*.js',
            'warehouse_3d_designer/static/src/**/*.scss',
            'warehouse_3d_designer/static/src/**/*.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
