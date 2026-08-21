# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anupriya Ashok (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Product Management',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Dashboard which displays top sales, purchases monthly
    movements and location categorization of Products.""",
    'description': """This module module for each product, accompanied by
    its dedicated dashboard. This dashboard should feature charts highlighting 
    the top-selling products, top-purchased products, and monthly product 
    movements. Additionally, include a section displaying products categorized 
    by location.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'license': 'LGPL-3',
    'depends': ['product', 'sale', 'purchase', 'stock'],
    'data': [
        'views/product_views.xml',
        'views/product_dashboard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js',
            'product_management_app/static/src/css/dashboard_views.css',
            'product_management_app/static/src/js/product_dashboard.js',
            'product_management_app/static/src/xml/dashboard.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
