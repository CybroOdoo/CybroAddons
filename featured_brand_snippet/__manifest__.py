# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Featured Brand Snippet',
    'version': '19.0.1.0.0',
    'category': 'Website/eCommerce',
    'summary': 'Dynamic snippet for displaying featured product brands',
    'description': """
        Display featured product brands in a dynamic carousel
        and allow customers to view the products of each brand.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'product_brand_sale',
        'website_sale',
    ],
    'data': [
        'views/product_brand_views.xml',
        'views/brand_snippet_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'featured_brand_snippet/static/src/xml/dynamic_brand_carousel.xml',
            'featured_brand_snippet/static/src/js/brand_selection.js',
            'featured_brand_snippet/static/src/scss/responsive_style.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
