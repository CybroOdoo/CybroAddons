# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    "name": "Point of Sale Signature",
    "version": "17.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Capture customer signature in POS",
    'description': """This app will save the customer signature to POS order""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["point_of_sale"],
    "data": ["views/pos_order_view.xml"],
    "assets": {
        'point_of_sale._assets_pos': [
            "point_of_sale_signature/static/src/js/order.js",
            "point_of_sale_signature/static/src/js/payment_screen_button.js",
            "point_of_sale_signature/static/src/js/signature_popup.js",
            "point_of_sale_signature/static/src/xml/order_receipt.xml",
            "point_of_sale_signature/static/src/xml/payment_screen_button.xml",
            "point_of_sale_signature/static/src/xml/signature_popup.xml",
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
