# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Adarsh K(<https://www.cybrosys.com>)
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
    'name': 'POS Cross-Selling',
    'version': '18.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': 'Cross Selling products in pos',
    'description': "This module is used for cross selling products in pos. "
                   "We can manage and use the cross-selling product in pos",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_cross_selling_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            '/pos_pro_cross_selling/static/src/app/cross_product/cross_product.js',
            '/pos_pro_cross_selling/static/src/app/cross_product/cross_product.xml',
            '/pos_pro_cross_selling/static/src/js/ProductItem.js',
            '/pos_pro_cross_selling/static/src/scss/cross_product.scss'
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
