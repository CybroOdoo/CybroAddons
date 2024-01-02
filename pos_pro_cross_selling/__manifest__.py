# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha K (odoo@cybrosys.com)
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
    'name': 'POS Cross-Selling',
    'version': '16.0.1.0.0',
    'category': 'Point Of Sale',
    'sequence': '20',
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
        'point_of_sale.assets': [
            '/pos_pro_cross_selling/static/src/js/CrossProduct.js',
            '/pos_pro_cross_selling/static/src/xml/cross_product_templates.xml',
            '/pos_pro_cross_selling/static/src/js/ProductItem.js',
            '/pos_pro_cross_selling/static/src/scss/cross_product.scss'
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
