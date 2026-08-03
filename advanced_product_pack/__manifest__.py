# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Advanced Product Pack',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Create and manage product bundle packs with auto-calculated prices and costs.',
    'description': """
                        Advanced Product Pack
                        =====================
                        This module allows users to create product bundle packs from Sales > Products > Product Pack menu.
                        Features:
                        - Auto calculate product bundle pack price and cost.
                        - Add multiple product items to a bundle pack.
                        - Prevent variants for product bundle packs.
                        - Filter products by 'Product Pack'.
                        """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'sale_management',
        'stock',
        'website_sale',
        'website_sale_stock',
        'sale_stock',
        'point_of_sale',
        'project',
        'sale_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_ribbon_data.xml',
        'views/product_bundle_line_views.xml',
        'views/product_template_views.xml',
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'advanced_product_pack/static/src/app/components/product_card/product_card.xml',
            'advanced_product_pack/static/src/app/components/orderline/orderline.xml',
            'advanced_product_pack/static/src/app/models/pos_order_line.js',
            'advanced_product_pack/static/src/scss/pos_bundle.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
