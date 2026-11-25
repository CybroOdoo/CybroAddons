###############################################################################
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
###############################################################################
{
    'name': 'POS Return Barcode',
    'version': '20.0.1.0.0',
    'summary': 'Return products effortlessly via receipt barcode scanning in Point of Sale.',
    'description': """This module prints a barcode on every Point of Sale
    receipt. When a customer comes back to return products, the cashier clicks
    the Return button, scans or types the receipt barcode, and the original
    order opens in the ticket screen, ready to be refunded. Orders that have
    already been refunded are not returned again, and receipts can also be
    searched by barcode in the ticket screen.""",
    'category': 'Point of Sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/pos_order_views.xml',
        'views/pos_order_receipt.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_return_barcode/static/src/js/return_product.js',
            'pos_return_barcode/static/src/js/barcode_popup.js',
            'pos_return_barcode/static/src/js/ticket_screen.js',
            'pos_return_barcode/static/src/js/generate_printer_data.js',
            'pos_return_barcode/static/src/xml/return_product_template.xml',
            'pos_return_barcode/static/src/xml/barcode_popup.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
