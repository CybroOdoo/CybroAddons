###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,pointless-statement,manifest-required-author,manifest-deprecated-key,manifest-superfluous-key
{
    'name': 'Advanced Product Pack',
    'version': '20.0.1.0.0',
    'summary': (
        'Create and manage product bundle packs with auto-calculated prices '
        'and costs.'
    ),
    'description': (
        'Advanced Product Pack allows users to create product bundle packs '
        'from Sales > Products > Product Pack menu. Features include auto '
        'calculation of bundle pack price and cost, multiple items in bundles, '
        'preventing variants for bundle packs, and filtering products by '
        'Product Pack.'
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Sales',
    'depends': [
        'sale_management',
        'stock',
        'website_sale',
        'sale_stock',
        'point_of_sale',
        'project',
        'sale_project',
    ],
    'data': [
        'security/ir.access.csv',
        'data/product_ribbon_data.xml',
        'views/product_template_views.xml',
        'views/website_sale_templates.xml',
        'views/pos_order_receipt.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'advanced_product_pack/static/src/app/components/product_card/product_card.xml',
            'advanced_product_pack/static/src/app/components/orderline/orderline.xml',
            'advanced_product_pack/static/src/app/models/pos_order_line.js',
            'advanced_product_pack/static/src/app/utils/generate_printer_data.js',
            'advanced_product_pack/static/src/scss/pos_bundle.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
