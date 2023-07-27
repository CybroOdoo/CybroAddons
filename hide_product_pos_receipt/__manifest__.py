# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
    'name': 'Hide Product In POS Receipt',
    'description': 'The "Hide Product in POS Receipt" feature allows users to '
                   'selectively hide certain products from appearing on the '
                   'point of sale (POS) receipt in Odoo.Enabling and '
                   'configuringthe"Hide Product in POS Receipt" feature is '
                   'straightforward and user-friendly. Once implemented, users'
                   'can easily test the changesby creating sales transactions '
                   'in the POS module and verifying the appearance of products'
                   ' on the receipt.',
    'summary': 'Hide Product In POS feature in Odoo offers businesses the'
               ' ability to selectively hide products from appearing on their'
               ' POS receipts. This improves the overall receipt layout  '
               'simplifies the customers purchasing experience',
    'category': 'Point of Sale',
    'version': '16.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': [
        'views/product_template_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'hide_product_pos_receipt/static/src/js/product_template.js',
            'hide_product_pos_receipt/static/src/js/receipt.js',
            'hide_product_pos_receipt/static/src/xml/receipt_templates.xml'
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
