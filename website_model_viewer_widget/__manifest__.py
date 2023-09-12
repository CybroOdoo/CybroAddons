# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Athira Premanand (<https://www.cybrosys.com>)
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
    'name': 'Website Model Viewer Widget',
    'version': '16.0.1.0.0',
    'category': 'Website,eCommerce',
    'summary': """Experience the product like never before with our stunning 3D
        model viewer.""",
    'description': """Website Model Viewer Widget app helps to explore every
                    angle and detail of the product right
                    from our website!""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'product', 'model_viewer_widget', 'website_sale'],
    'data': [
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'https://unpkg.com/@egjs/view3d@2.10.1/dist/view3d.pkgd.min.js',
            'website_model_viewer_widget/static/src/js/3d_product_view.js',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}