# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Featured Brand Snippet',
    'version': '16.0.1.0.0',
    'category': 'Website,eCommerce',
    'summary': 'Dynamic snippet for selecting brands',
    'description': 'Featured brands are arranged in a carousel and allows to view the products of selected brand',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': ['product_brand_sale', 'website_sale'],
    'data': [
        'views/product_brand_views.xml',
        'views/brand_snippet_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'featured_brand_snippet/static/src/xml/dynamic_brand_courosel.xml',
            'featured_brand_snippet/static/src/js/brand_selection.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
