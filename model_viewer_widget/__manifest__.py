# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shikhil Raj (odoo@cybrosys.com)
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
###############################################################################
{
    'name': '3D Image Viewer Widget',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Upload a GLB file on a product and view it as an interactive 3D model.',
    'description': """Adds a 3D Model Viewer page to the product form. Upload a
     GLB file, then rotate and zoom the model directly in the backend.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['product', 'web'],
    'data': [
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'model_viewer_widget/static/src/js/widget.js',
            'model_viewer_widget/static/src/scss/widget.scss',
            'model_viewer_widget/static/src/xml/widget.xml',
        ],
        'web.assets_tests': [
            'model_viewer_widget/static/tests/tours/*.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
