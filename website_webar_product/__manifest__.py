# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Website WebAR Product Viewer',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Realistic view of the product in website',
    'description': """This module helps to view Website Products in 3D.
     The customers can experience interactive AR commerce using WebAR 
     technology.This gives customers a realistic view of the product, show how
     it will look in real-life environments.""",
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        "views/product_template_views.xml",
        "views/website_sale_templates.xml",
    ],
    'demo': ["data/product_template_demo.xml"],
    'assets': {
        'web.assets_frontend': [
            '/website_webar_product/static/src/js/website_product_view.js',
            '/website_webar_product/static/src/css/website_product_view.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
