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
    'name': "Pos Product Magnify Image",
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Magnify product image in PoS""",
    'description': "Allows to enlarge the image in a button click for every"
                   "product in PoS",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
    'depends': ['point_of_sale', 'web'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_magnify_image/static/src/js/MagnifyProductPopup.js',
            'pos_magnify_image/static/src/xml/MagnifyProductPopup.xml',
            'pos_magnify_image/static/src/js/prouct_magnify_image.js',
            'pos_magnify_image/static/src/xml/product_magnify_image.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
