# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Portal Product Availability",
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': """Portal Product Availability""",
    'description': """Portal Users Can Check The Availability of Products""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'depends': ['portal', 'sale_management', 'stock', 'contacts',
                'website_sale'],

    'data': [
        'views/portal_inherited.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'portal_stock_check/static/src/js/search_products.js',
            'portal_stock_check/static/src/xml/product_list.xml'
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
