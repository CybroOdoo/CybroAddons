# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Thasni CP(odoo@cybrosys.com)
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
    'name': "Product 360 Degree View in Website",
    'version': '16.0.1.0.0',
    'category': 'eCommerce',
    'summary': """To see the product from all angles in eCommerce.""",
    'description': "By configuring different photos, this module enables us to "
                   "view products in 360 degrees, giving us access to all"
                   " of their angles",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['product', 'website_sale'],
    'data': ['security/ir.model.access.csv',
             'views/product_template_views.xml',
             'views/product_product_views.xml',
             'views/360_view_templates.xml',
             ],
    'assets': {'web.assets_frontend': [
        'product_360_degree_view_in_website/static/src/js/360_view.js',
        'product_360_degree_view_in_website/static/src/css/360_view.css'
    ], },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
