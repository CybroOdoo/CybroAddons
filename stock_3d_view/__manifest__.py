# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Stock 3D View",
    'version': '16.0.1.0.0',
    'category': 'Warehouse',
    'summary': """Virtual 3D Visualization of warehouses and Locations""",
    'description': """This module innovative addition to the inventory and 
     warehouse management module, enhancing the traditional methods of tracking 
     stock and warehouse operations. Leveraging advanced visualization 
     technology, this app provides users with an immersive and dynamic 
     three-dimensional representation of their warehouses, inventory items, and 
     stock movements.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['stock', 'web'],
    'data': [
        'views/stock_location_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/stock_3d_view/static/src/js/form_3d_view.js',
            '/stock_3d_view/static/src/js/listview_3d.js',
            '/stock_3d_view/static/src/css/3d_view.scss',
            'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.js',
            'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
            "https://cdn.jsdelivr.net/npm/three@0.122.0/examples/js/controls/OrbitControls.min.js",
            'stock_3d_view/static/src/xml/stock_location_3d_templates.xml',
            'stock_3d_view/static/src/xml/stock_location_breadcrumb_templates.xml',
            'stock_3d_view/static/src/xml/stock_location_modal_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
