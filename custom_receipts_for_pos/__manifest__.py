# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
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
    'name': 'Custom Receipts For POS',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Customizable Point of Sale Receipt Designs with multiple 
    templates support""",
    'description': """The Custom Receipts for POS module empowers users to 
    create and manage highly customized receipt designs tailored to their brand 
    identity. By leveraging Odoo's modern OWL framework, this module provides
    a flexible way to update receipt layouts without complex technical overhead.
    Key Features:
    - Customizable Receipts: Design unique templates for different Point of Sale 
    instances.
    - Multiple Templates Support: Easily switch between various receipt styles.
    - Professional Templates: Enhances the customer experience with 
    well-formatted and stylish receipts.
    - Seamless Integration: Works natively with Odoo 19 Point of Sale.
    - Reliable Fallback: Automatically reverts to the default POS receipt if a 
    custom design is not selected.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/pos_receipt_data.xml',
        'views/pos_receipt_views.xml',
        'views/pos_config_views.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'custom_receipts_for_pos/static/src/app/receipt_design.js',
            'custom_receipts_for_pos/static/src/app/order_receipt.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
